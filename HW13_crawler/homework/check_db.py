"""Проверка содержимого БД"""
import sqlite3

conn = sqlite3.connect('hackernews.db')
cursor = conn.cursor()

print("=" * 70)
print("STORIES:")
print("=" * 70)
cursor.execute('SELECT id, title, score, descendants FROM stories ORDER BY score DESC')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Score: {row[2]}, Comments: {row[3]}")
    print(f"   Title: {row[1]}")
    print()

print("=" * 70)
print("STATISTICS:")
print("=" * 70)
cursor.execute('SELECT COUNT(*) FROM stories')
print(f"Total stories: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM comments')
print(f"Total comments: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM comment_links')
print(f"Total links extracted: {cursor.fetchone()[0]}")

conn.close()
