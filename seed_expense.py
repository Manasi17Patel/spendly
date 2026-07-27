#!/usr/bin/env python3
"""
Seed expenses for a specific user.
Usage: /seed-expenses <user_id> <count> <months>
Example: /seed-expenses 1 50 6
"""
import argparse
import sys
import os
import random
from datetime import date, timedelta

# Add the project root to the path so we can import from database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import get_db

def main():
    parser = argparse.ArgumentParser(description='Seed expenses for a user')
    parser.add_argument('user_id', type=int, help='User ID')
    parser.add_argument('count', type=int, help='Number of expenses to create')
    parser.add_argument('months', type=int, help='How many past months to spread them across')

    args = parser.parse_args()

    user_id = args.user_id
    count = args.count
    months = args.months

    # Validate arguments
    if user_id <= 0 or count <= 0 or months <= 0:
        print("Error: All arguments must be positive integers")
        sys.exit(1)

    conn = get_db()
    try:
        # Verify user exists
        cursor = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            print(f"No user found with id {user_id}")
            sys.exit(1)

        # Define categories with weights and amount ranges
        categories = [
            ('Food', 30, 50, 800),
            ('Transport', 20, 20, 500),
            ('Bills', 15, 200, 3000),
            ('Health', 10, 100, 2000),
            ('Entertainment', 10, 100, 1500),
            ('Shopping', 10, 200, 5000),
            ('Other', 5, 50, 1000)
        ]

        # Descriptions for each category (Indian context)
        descriptions = {
            'Food': [
                'Groceries from local store',
                'Lunch at restaurant',
                'Dinner with family',
                'Snacks and tea',
                'Food delivery order',
                'Breakfast at cafe',
                'Weekend dinner',
                'Fruits and vegetables',
                'Milk and dairy',
                'Rice and lentils'
            ],
            'Transport': [
                'Auto rickshaw fare',
                'Bus ticket',
                'Metro recharge',
                'Fuel for bike',
                'Cab ride to office',
                'Parking fees',
                'Train ticket',
                'Vehicle maintenance',
                'Toll charges',
                'Bike service'
            ],
            'Bills': [
                'Electricity bill',
                'Water bill',
                'Gas cylinder',
                'Internet recharge',
                'Mobile phone bill',
                'DTH/cable TV',
                'LPG subsidy',
                'Society maintenance',
                'Property tax',
                'Washing machine repair'
            ],
            'Health': [
                'Doctor consultation',
                'Medicines from pharmacy',
                'Dental checkup',
                'Eye test and glasses',
                'Blood test',
                'Vitamins and supplements',
                'Ayurvedic treatment',
                'Homeopathy consultation',
                'Fitness center fee',
                'Yoga classes'
            ],
            'Entertainment': [
                'Movie tickets',
                'Concert show',
                'Amusement park',
                'Streaming subscription',
                'Game zone',
                'Theatre play',
                'Comedy show',
                'Sports match tickets',
                'Museum entry',
                'Boating ride'
            ],
            'Shopping': [
                'Clothes from market',
                'Footwear purchase',
                'Electronics accessory',
                'Gift for friend',
                'Home decor item',
                'Kitchen utensils',
                'Books and stationery',
                'Personal grooming',
                'Jewelry purchase',
                'Diwali shopping'
            ],
            'Other': [
                'Charity donation',
                'Postage and courier',
                'Printing and photocopy',
                'Stationery items',
                'Haircut and salon',
                'Laundry services',
                'Duplicate keys',
                'Umbrella purchase',
                'Raincoat',
                'Battery replacement'
            ]
        }

        # Calculate date range: today minus months months
        end_date = date.today()
        start_date = end_date - timedelta(days=30*months)  # Approximate

        # Prepare data for insertion
        expenses_data = []

        # Generate random expenses
        for _ in range(count):
            # Choose category based on weights
            category = random.choices(
                [c[0] for c in categories],
                weights=[c[1] for c in categories]
            )[0]

            # Get amount range for this category
            min_amt = next(c[2] for c in categories if c[0] == category)
            max_amt = next(c[3] for c in categories if c[0] == category)
            amount = round(random.uniform(min_amt, max_amt), 2)

            # Generate random date within the range
            days_between = (end_date - start_date).days
            random_days = random.randrange(days_between)
            expense_date = start_date + timedelta(days=random_days)

            # Get a random description for this category
            description = random.choice(descriptions[category])

            expenses_data.append((
                user_id,
                amount,
                category,
                expense_date.isoformat(),
                description
            ))

        # Insert all expenses in a single transaction
        conn.execute('BEGIN TRANSACTION')
        try:
            conn.executemany('''
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
            ''', expenses_data)
            conn.commit()

            # Get the actual date range of inserted expenses
            cursor = conn.execute('''
                SELECT MIN(date) as min_date, MAX(date) as max_date
                FROM expenses WHERE user_id = ?
            ''', (user_id,))
            date_range = cursor.fetchone()

            # Get a sample of 5 inserted records
            cursor = conn.execute('''
                SELECT id, amount, category, date, description
                FROM expenses WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 5
            ''', (user_id,))
            sample = cursor.fetchall()

            print(f"Successfully inserted {count} expenses for user {user_id}")
            print(f"Date range: {date_range['min_date']} to {date_range['max_date']}")
            print("\nSample of 5 inserted records:")
            print("ID | Amount (Rs) | Category | Date | Description")
            print("-" * 80)
            for exp in sample:
                print(f"{exp['id']:3} | {exp['amount']:8.2f} | {exp['category']:12} | {exp['date']:10} | {exp['description']}")

        except Exception as e:
            conn.rollback()
            print(f"Error inserting expenses: {e}")
            sys.exit(1)

    finally:
        conn.close()

if __name__ == '__main__':
    main()