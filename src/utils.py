# cython: language_level=3
from markdown import markdown
from bs4 import BeautifulSoup, Tag

TAG_STYLES = {
    'h1': 'text-4xl font-extrabold text-slate-900 dark:text-slate-100 mb-6 mt-8 scroll-mt-24 flex justify-between items-center border-b border-slate-200 dark:border-slate-700 pb-2',
    'h2': 'text-3xl font-bold text-slate-800 dark:text-slate-100 mb-5 mt-7 scroll-mt-24 flex justify-between items-center',
    'h3': 'text-2xl font-semibold text-slate-800 dark:text-slate-100 mb-4 mt-6 flex justify-between items-center',
    'h4': 'text-xl font-medium text-slate-700 dark:text-slate-200 mb-3 mt-5',
    'h5': 'text-lg font-medium text-slate-700 dark:text-slate-200 mb-2 mt-4',
    'h6': 'text-base font-medium text-slate-600 dark:text-slate-300 mb-1 mt-3',
    'p': 'mb-4 text-slate-700 dark:text-slate-200 leading-relaxed tracking-normal',
    'ul': 'list-disc list-inside pl-6 mb-4 text-slate-700 dark:text-slate-200',
    'ol': 'list-decimal list-inside pl-6 mb-4 text-slate-700 dark:text-slate-200',
    'li': 'mb-1',
    'blockquote': 'border-l-4 border-cyan-500 pl-6 italic text-slate-700 dark:text-slate-200 bg-cyan-50 dark:bg-slate-800 py-3 px-4 rounded-md my-6',
    'hr': 'my-8 border-t border-slate-300 dark:border-slate-700',
    'a': 'text-cyan-700 dark:text-cyan-300 hover:text-cyan-900 dark:hover:text-cyan-200 underline',
    'code': 'bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-sm font-mono text-indigo-700 dark:text-indigo-300',
    'pre': 'bg-slate-900 text-slate-100 p-5 rounded-lg overflow-x-auto text-sm shadow-inner my-6 whitespace-pre-wrap break-words border border-slate-700',
    'table': 'table-auto w-full border-collapse border border-slate-300 dark:border-slate-700 shadow-sm my-8 text-sm',
    'thead': 'bg-slate-100 dark:bg-slate-800',
    'th': 'border border-slate-300 dark:border-slate-700 px-4 py-3 text-left bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold',
    'td': 'border border-slate-300 dark:border-slate-700 px-4 py-2 text-slate-700 dark:text-slate-200'
}

HEADING_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

def wrap_collapsible_sections(soup):
    """
    For each heading (h1-h3), wrap all content until the next heading of same or higher level
    inside a collapsible div.
    """
    for heading in soup.find_all(HEADING_TAGS):
        level = int(heading.name[1])
        toggle_id = f"section-{id(heading)}"
        content_div = soup.new_tag("div", id=toggle_id, **{"class": "collapsible-content"})

        # Gather all siblings until the next heading of the same or higher level
        sibling = heading.find_next_sibling()
        while sibling:
            # Stop if next heading of same or higher level
            if sibling.name in HEADING_TAGS and int(sibling.name[1]) <= level:
                break
            next_sibling = sibling.find_next_sibling()
            content_div.append(sibling.extract())
            sibling = next_sibling

        # Only insert if we actually gathered content
        if content_div.contents:
            heading.insert_after(content_div)

            # Add toggle button
            toggle_button = soup.new_tag(
                "button",
                **{
                    'class': 'toggle-button text-cyan-700 dark:text-cyan-300 text-xl font-bold ml-2 focus:outline-none',
                    'onclick': f"toggleContent('{toggle_id}', this)"
                }
            )
            toggle_button.string = '+'
            heading.append(toggle_button)

def apply_tailwind_classes(soup):
    for tag_name, classes in TAG_STYLES.items():
        for el in soup.find_all(tag_name):
            if tag_name == 'code' and el.parent.name == 'pre':
                continue
            existing_classes = el.get('class', [])
            el['class'] = list(set(existing_classes + classes.split()))
            if tag_name == 'a':
                el['target'] = '_blank'
                el['rel'] = 'noopener noreferrer'

def handle_special_formatting(soup):
    for code in soup.find_all('code'):
        if code.parent.name != 'pre':
            code['class'] = TAG_STYLES['code'].split()
    # Checkbox syntax left as is

def group_labelled_list_items(soup):
    for ul in soup.find_all(['ul', 'ol']):
        li_list = ul.find_all('li', recursive=False)
        i = 0
        while i < len(li_list):
            li = li_list[i]
            if li.get_text(strip=True).endswith(':') and (not li.find('ul')):
                sub_ul = soup.new_tag('ul')
                j = i + 1
                while j < len(li_list):
                    next_li = li_list[j]
                    if (next_li.find('strong', recursive=False) or 
                        next_li.get_text(strip=True).endswith(':')):
                        break
                    sub_ul.append(next_li.extract())
                    li_list.pop(j)
                if sub_ul.contents:
                    li.append(sub_ul)
            i += 1

def render_minutes_with_tailwind(md_text: str) -> str:
    html = markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br', 'extra'])
    soup = BeautifulSoup(html, 'html.parser')

    group_labelled_list_items(soup)
    wrap_collapsible_sections(soup)
    handle_special_formatting(soup)
    apply_tailwind_classes(soup)
    return str(soup)

if __name__ == "__main__":
    with open("data.md", "r") as f:
        md_text = f.read()
    html = render_minutes_with_tailwind(md_text)
    with open("output.html", "w") as f:
        f.write(html)