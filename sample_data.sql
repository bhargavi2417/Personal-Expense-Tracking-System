-- Sample (fictional) data for the Personal Expense Tracking System.
-- Run this only ONCE (python init_db.py --sample does that check for you).

USE expense_tracker;

INSERT IGNORE INTO categories (name, description) VALUES
    ('Food', 'Meals, groceries and snacks'),
    ('Transport', 'Bus, metro, fuel and cabs'),
    ('Rent', 'Hostel or house rent'),
    ('Utilities', 'Mobile, internet and electricity'),
    ('Entertainment', 'Movies, games and outings'),
    ('Health', 'Medicines and check-ups'),
    ('Education', 'Books, courses and printing'),
    ('Shopping', 'Clothes and personal items'),
    ('Other', 'Anything else');

INSERT INTO expenses (title, amount, expense_date, category_id, notes) VALUES
    ('Hostel mess fee', 3500.00, '2026-07-01', (SELECT id FROM categories WHERE name = 'Rent'), 'Monthly mess and room fee'),
    ('Groceries', 640.50, '2026-07-03', (SELECT id FROM categories WHERE name = 'Food'), NULL),
    ('Metro card recharge', 300.00, '2026-07-05', (SELECT id FROM categories WHERE name = 'Transport'), NULL),
    ('Mobile recharge', 299.00, '2026-07-07', (SELECT id FROM categories WHERE name = 'Utilities'), 'Monthly plan'),
    ('Python book', 450.00, '2026-07-10', (SELECT id FROM categories WHERE name = 'Education'), 'Second-hand copy'),
    ('Movie with friends', 360.00, '2026-07-14', (SELECT id FROM categories WHERE name = 'Entertainment'), NULL),
    ('Pharmacy', 180.75, '2026-07-18', (SELECT id FROM categories WHERE name = 'Health'), 'Cold medicine'),
    ('Canteen lunch', 95.00, '2026-07-22', (SELECT id FROM categories WHERE name = 'Food'), NULL),
    ('T-shirt', 799.00, '2026-07-26', (SELECT id FROM categories WHERE name = 'Shopping'), NULL),
    ('Hostel mess fee', 3500.00, '2026-08-01', (SELECT id FROM categories WHERE name = 'Rent'), 'Monthly mess and room fee'),
    ('Groceries', 712.25, '2026-08-04', (SELECT id FROM categories WHERE name = 'Food'), NULL),
    ('Bus pass', 250.00, '2026-08-06', (SELECT id FROM categories WHERE name = 'Transport'), NULL),
    ('Internet bill', 499.00, '2026-08-08', (SELECT id FROM categories WHERE name = 'Utilities'), NULL),
    ('Lab record and printing', 220.00, '2026-08-12', (SELECT id FROM categories WHERE name = 'Education'), NULL),
    ('Birthday dinner', 850.00, '2026-08-16', (SELECT id FROM categories WHERE name = 'Food'), 'Friend''s birthday'),
    ('Cab to station', 410.00, '2026-08-20', (SELECT id FROM categories WHERE name = 'Transport'), NULL),
    ('Gaming subscription', 199.00, '2026-08-24', (SELECT id FROM categories WHERE name = 'Entertainment'), NULL),
    ('Headphones', 1299.00, '2026-08-28', (SELECT id FROM categories WHERE name = 'Shopping'), NULL),
    ('Hostel mess fee', 3500.00, '2026-09-01', (SELECT id FROM categories WHERE name = 'Rent'), 'Monthly mess and room fee'),
    ('Groceries', 598.00, '2026-09-03', (SELECT id FROM categories WHERE name = 'Food'), NULL),
    ('Mobile recharge', 299.00, '2026-09-07', (SELECT id FROM categories WHERE name = 'Utilities'), 'Monthly plan'),
    ('Online course', 999.00, '2026-09-10', (SELECT id FROM categories WHERE name = 'Education'), 'Data science basics'),
    ('Doctor consultation', 300.00, '2026-09-13', (SELECT id FROM categories WHERE name = 'Health'), NULL),
    ('Bus tickets home', 520.00, '2026-09-17', (SELECT id FROM categories WHERE name = 'Transport'), 'Festival trip'),
    ('Snacks and tea', 140.00, '2026-09-21', (SELECT id FROM categories WHERE name = 'Food'), NULL),
    ('Cricket match tickets', 600.00, '2026-09-25', (SELECT id FROM categories WHERE name = 'Entertainment'), NULL),
    ('Hostel mess fee', 3500.00, '2026-10-01', (SELECT id FROM categories WHERE name = 'Rent'), 'Monthly mess and room fee'),
    ('Groceries', 655.40, '2026-10-03', (SELECT id FROM categories WHERE name = 'Food'), NULL),
    ('Electricity share', 420.00, '2026-10-05', (SELECT id FROM categories WHERE name = 'Utilities'), NULL),
    ('Metro card recharge', 300.00, '2026-10-08', (SELECT id FROM categories WHERE name = 'Transport'), NULL),
    ('Project printing', 260.00, '2026-10-11', (SELECT id FROM categories WHERE name = 'Education'), 'Report and binding'),
    ('Shoes', 1499.00, '2026-10-14', (SELECT id FROM categories WHERE name = 'Shopping'), NULL),
    ('Weekend dinner', 540.00, '2026-10-17', (SELECT id FROM categories WHERE name = 'Food'), NULL),
    ('Gift for cousin', 700.00, '2026-10-19', (SELECT id FROM categories WHERE name = 'Other'), NULL);
