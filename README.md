#  Mini Relational Database in Python

A SQL database engine developed entirely from scratch in Python, designed for educational purposes and to deeply understand how relational database management systems (RDBMS) work under the hood.

##  Supported Features
The engine can parse and execute the main SQL clauses and functions:
- **Basic DDL / DML**: Table creation with custom data types and row insertion.
- **Projections and Filters**: `SELECT` clause (supporting `*` or specific columns) and advanced filtering with `WHERE` (operators `=`, `>`, `<`, `>=`, `<=`).
- **Sorting**: `ORDER BY` clause (`ASC` or `DESC`).
- **Grouping and Group Filters**: `GROUP BY` clauses (including multi-column) and `HAVING`.
- **Aggregation Functions**: `COUNT`, `MIN`, `MAX`, `SUM`, and `AVG` (both global and grouped).
- **Relations (JOIN)**: `Inner JOIN` operation between tables based on foreign keys via the `ON` clause.

##  How to Run It
1. Make sure you have Python installed on your computer.
2. Download or clone the repository.
3. Run the main script:
   ```bash
   python script.py