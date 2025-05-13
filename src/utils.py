from markdown import markdown
from bs4 import BeautifulSoup

def render_minutes_with_tailwind(md_text):
    html = markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])
    soup = BeautifulSoup(html, 'html.parser')

    # Headings
    heading_styles = {
        'h1': 'text-3xl font-extrabold text-indigo-700 mb-4 mt-6',
        'h2': 'text-2xl font-bold text-indigo-600 mb-3 mt-5',
        'h3': 'text-xl font-semibold text-indigo-500 mb-2 mt-4',
        'h4': 'text-lg font-medium text-indigo-400 mb-2 mt-3',
        'h5': 'text-base font-medium text-indigo-300 mb-1 mt-2',
        'h6': 'text-sm font-medium text-indigo-200 mb-1 mt-2',
    }

    for tag, classes in heading_styles.items():
        for el in soup.find_all(tag):
            el['class'] = classes

    # Paragraphs
    for tag in soup.find_all('p'):
        tag['class'] = 'mb-4 text-gray-800 leading-relaxed'

    # Lists
    for tag in soup.find_all('ul'):
        tag['class'] = 'list-disc list-inside ml-6 mb-4 text-gray-800'
    for tag in soup.find_all('ol'):
        tag['class'] = 'list-decimal list-inside ml-6 mb-4 text-gray-800'
    for tag in soup.find_all('li'):
        tag['class'] = 'mb-1'

    # Blockquotes
    for tag in soup.find_all('blockquote'):
        tag['class'] = 'border-l-4 border-blue-400 pl-4 italic text-gray-600 bg-blue-50 py-2 px-3 rounded my-4'

    # Horizontal Rules
    for tag in soup.find_all('hr'):
        tag['class'] = 'my-6 border-t border-gray-300'

    # Links
    for tag in soup.find_all('a'):
        tag['class'] = 'text-blue-600 underline hover:text-blue-800'
        tag['target'] = '_blank'

    # Code
    for tag in soup.find_all('code'):
        tag['class'] = 'bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-purple-600'
    for tag in soup.find_all('pre'):
        tag['class'] = 'bg-gray-900 text-green-200 p-4 rounded overflow-x-auto text-sm shadow-inner my-4'

    # Tables
    for tag in soup.find_all('table'):
        tag['class'] = 'table-auto w-full border-collapse border border-gray-300 my-6'
    for tag in soup.find_all('thead'):
        tag['class'] = 'bg-gray-100'
    for tag in soup.find_all('th'):
        tag['class'] = 'border px-4 py-2 text-left bg-gray-200 text-gray-700 font-semibold'
    for tag in soup.find_all('td'):
        tag['class'] = 'border px-4 py-2 text-gray-800'

    return str(soup)
