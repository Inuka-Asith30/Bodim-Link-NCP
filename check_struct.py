import os

with open('templates/boarding_details.html', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to find a place to insert the reviews section.
# Usually, before the closing </main> or closing </div> of the main content.
# Let's see the structure of boarding_details.html
