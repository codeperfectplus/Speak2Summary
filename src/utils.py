from markdown import markdown
from bs4 import BeautifulSoup

def render_minutes_with_tailwind(md_text):
    html = markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])
    soup = BeautifulSoup(html, 'html.parser')

    # Headings – updated for white background
    heading_styles = {
        'h1': 'text-4xl font-extrabold text-indigo-800 mb-6 mt-8',
        'h2': 'text-3xl font-bold text-indigo-700 mb-5 mt-7',
        'h3': 'text-2xl font-semibold text-indigo-600 mb-4 mt-6',
        'h4': 'text-xl font-medium text-indigo-500 mb-3 mt-5',
        'h5': 'text-lg font-medium text-indigo-400 mb-2 mt-4',
        'h6': 'text-base font-medium text-indigo-300 mb-1 mt-3',
    }
    for tag, classes in heading_styles.items():
        for el in soup.find_all(tag):
            el['class'] = classes + ' scroll-mt-24'  # type: ignore

    # Paragraphs
    for tag in soup.find_all('p'):
        tag['class'] = 'mb-4 text-gray-800 leading-relaxed tracking-normal'  # type: ignore

    # Lists
    for tag in soup.find_all('ul'):
        tag['class'] = 'list-disc list-inside pl-6 mb-4 text-gray-800'  # type: ignore
    for tag in soup.find_all('ol'):
        tag['class'] = 'list-decimal list-inside pl-6 mb-4 text-gray-800'  # type: ignore
    for tag in soup.find_all('li'):
        tag['class'] = 'mb-1'  # type: ignore

    # Blockquotes
    for tag in soup.find_all('blockquote'):
        tag['class'] = (
            'border-l-4 border-blue-400 pl-6 italic text-gray-700 '
            'bg-blue-50 py-3 px-4 rounded-md my-6'
        )  # type: ignore

    # Horizontal Rules
    for tag in soup.find_all('hr'):
        tag['class'] = 'my-8 border-t border-gray-300'  # type: ignore

    # Links
    for tag in soup.find_all('a'):
        tag['class'] = 'text-blue-700 hover:text-blue-900 underline'  # type: ignore
        tag['target'] = '_blank'  # type: ignore
        tag['rel'] = 'noopener noreferrer'  # type: ignore

    # Inline Code
    for tag in soup.find_all('code'):
        if tag.parent.name != 'pre':  # type: ignore
            tag['class'] = 'bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-purple-700'  # type: ignore

    # Code Blocks
    for tag in soup.find_all('pre'):
        tag['class'] = (
            'bg-gray-100 text-gray-800 p-5 rounded-lg overflow-x-auto text-sm '
            'shadow-inner my-6 whitespace-pre-wrap break-words'
        )  # type: ignore

    # Tables
    for tag in soup.find_all('table'):
        tag['class'] = 'table-auto w-full border-collapse border border-gray-300 shadow-sm my-8 text-sm'  # type: ignore
    for tag in soup.find_all('thead'):
        tag['class'] = 'bg-gray-100'  # type: ignore
    for tag in soup.find_all('th'):
        tag['class'] = 'border px-4 py-3 text-left bg-gray-200 text-gray-700 font-semibold'  # type: ignore
    for tag in soup.find_all('td'):
        tag['class'] = 'border px-4 py-2 text-gray-800'  # type: ignore

    return str(soup)
