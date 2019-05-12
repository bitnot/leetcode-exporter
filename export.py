from itertools import chain, islice
import os
import re
import requests
from time import sleep
from string import Template


# Store the value of you cookies in 'cookies.txt'
COOKIES = open('cookies.txt', 'r').read().strip().replace('cookie: ', '', 1)
# Change output dir if you like
LEETCODE_DIR = '../leetcode-solutions'
SUBMISSIONS_URL = 'https://leetcode.com/api/submissions/?offset={}&limit={}'
GRAPHQL_URL = 'https://leetcode.com/graphql'
THROTTLE_SECONDS = 1
EXTENSIONS = {
    "cpp": 'cpp',
    "java": 'java',
    "python": 'py',
    "python3": 'py',
    "mysql": 'sql',
    "mssql": 'sql',
    "oraclesql": 'sql',
    "c": 'c',
    "csharp": 'cs',
    "javascript": 'js',
    "ruby": 'rb',
    "bash": 'sh',
    "swift": 'swift',
    "golang": 'go',
    "scala": 'scala',
    "html": 'html',
    "pythonml": 'py',
    "kotlin": 'kt',
    "rust": 'rs',
    "php": 'php'
}
SLUG_RE = re.compile(r"[^-0-9a-z ]", re.IGNORECASE)
DESCRIPTION_TEMPLATE = Template("""
<!doctype html>
<html>
    <head>
        <title>${difficulty}: ${title}</title>
    <head>
    <body>
        <h1>${title} (${difficulty})</h1>
        <a href='https://leetcode.com/${url}'>View on LeetCode</a></br></hr>
        ${content}
    </body>
</html>
""")


def question_data(slug):
    return {
        "operationName": "questionData",
        "variables": {
            "titleSlug": slug
        },
        "query": """query questionData($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                questionFrontendId
                boundTopicId
                title
                titleSlug
                content
                difficulty
                sampleTestCase
            }
        }"""
    }


def get_submissions(batch_size=20):
    """Gets all submissions in `batch_size` chunks"""
    offset = 0
    while True:
        response = requests.get(SUBMISSIONS_URL.format(
            offset, batch_size), headers={'Cookie': COOKIES})
        json_response = response.json()
        if 'detail' in json_response:
            print(json_response['detail'])
        if 'submissions_dump' in json_response:
            yield json_response['submissions_dump']
        if not 'has_next' in json_response or not json_response['has_next']:
            break
        offset += 1
        sleep(THROTTLE_SECONDS)


def add_description(submission_json):
    title = submission_json['title']
    slug = title_to_slug(title)
    print('{}: getting description'.format(slug))
    response = requests.post(GRAPHQL_URL, json=question_data(
        slug), headers={'Cookie': COOKIES})
    json_response = response.json()
    return {**submission_json, **json_response['data']['question'], 'slug': slug}


def is_accepted(submission_json):
    return 'status_display' in submission_json and submission_json['status_display'] == 'Accepted'


def title_to_slug(title):
    return SLUG_RE.sub("", title).replace(" ", "-").lower()


def store_solution(solution):
    slug = solution['slug']
    print('{}: storing'.format(slug))
    solution_dir = LEETCODE_DIR + '/' + slug + '/'
    if not os.path.exists(solution_dir):
        os.makedirs(solution_dir)

        description_file = open(solution_dir+'index.html', 'w')
        description_file.write(DESCRIPTION_TEMPLATE.substitute(solution))
        description_file.close

        test_file = open(solution_dir+'input.txt', 'w')
        test_file.write(solution['sampleTestCase'])
        test_file.close

    filename = solution_dir + 'solution-{}.{}'.format(solution['id'],
                                       EXTENSIONS[solution['lang']])
    if not os.path.exists(filename):
        print('{}: writing solution #{}'.format(slug, solution['id'],))
        solution_file = open(filename, 'w')
        solution_file.write(solution['code'])
        solution_file.close
    else:
        print('{}: skipping solution #{} - already exists'.format(slug, solution['id'],))



submissions = chain.from_iterable(get_submissions())
accepted_submissions = filter(is_accepted, submissions)
accepted_submissions_details = map(add_description, accepted_submissions)
for solution in accepted_submissions_details:
    store_solution(solution)
