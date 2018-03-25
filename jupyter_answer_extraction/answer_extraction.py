#!/usr/bin/env python

from __future__ import print_function
import sys
import json

from jupyter_answer_extraction.structs import Answer

def print_usage():
    print('Usage: answer_extraction.py <full_notebook_path>.ipynb <answer_notebook_path>.ipynb' +
          ' <answer_symbol>\n\nThe last argument is optional and is only used if the answer cells' +
          ' do not have the "group" metadata attribute')

def extract_group_answer(group, cells):
    answer_list = list()
    for cell in cells:
        if 'group' in cell['metadata'] and cell['metadata']['group'] == group:
            answer_data = Answer()
            answer_data.question_id = group
            answer_data.answer = cell['source']
            answer_data.cell_type = cell['cell_type']
            if answer_data.cell_type == 'code':
                answer_data.cell_outputs = cell['outputs']
            answer_list.append(answer_data)
    return answer_list

def extract_answers_from_alternating_cells(group, cells):
    answers = list()
    question_counter = 1
    for cell in cells:
        if 'group' in cell['metadata'] and cell['metadata']['group'] == group:
            answer_data = Answer()
            answer_data.question_id = str(question_counter)
            answer_data.answer = cell['source']
            answer_data.cell_type = cell['cell_type']
            if answer_data.cell_type == 'code':
                answer_data.cell_outputs = cell['outputs']
            answers.append(answer_data)
            question_counter += 1
    return answers

def extract_answers_from_marked_cells(cells, answer_symbol):
    answers = list()
    question_counter = 0
    for cell in cells:
        answer_symbol_idx = cell['source'][0].lower().find(answer_symbol)
        if answer_symbol_idx != -1:
            answer_data = Answer()
            answer_data.question_id = str(question_counter)
            answer_data.answer = cell['source']
            answer_data.answer[0] = answer_data.answer[0][answer_symbol_idx +
                                                          len(answer_symbol):].strip()
            answer_data.cell_type = cell['cell_type']
            if answer_data.cell_type == 'code':
                answer_data.cell_outputs = cell['outputs']
            answers.append(answer_data)
            question_counter += 1
        else:
            question_idx = cell['source'][0].lower().find('question')
            if question_idx != -1:
                question_counter += 1
    return answers

def generate_notebook_from_answer_dict(notebook_data, answers):
    print('Generating answer notebook from answer dictionary...')
    resulting_notebook_content = dict()
    resulting_notebook_content['metadata'] = notebook_data['metadata']
    resulting_notebook_content['nbformat'] = notebook_data['nbformat']
    resulting_notebook_content['nbformat_minor'] = notebook_data['nbformat_minor']
    resulting_notebook_content['cells'] = list()

    for group in sorted(answers.keys()):
        answer_id_cell_data = dict()
        answer_id_cell_data['cell_type'] = 'markdown'
        answer_id_cell_data['metadata'] = dict()
        answer_id_cell_data['source'] = ['# ' + group]
        resulting_notebook_content['cells'].append(answer_id_cell_data)

        for answer_data in answers[group]:
            answer_cell_data = dict()
            answer_cell_data['cell_type'] = answer_data.cell_type
            if answer_data.cell_type == 'code':
                answer_cell_data['outputs'] = answer_data.cell_outputs
                answer_cell_data['execution_count'] = None

            answer_cell_data['metadata'] = dict()
            answer_cell_data['metadata']['group'] = answer_data.question_id
            answer_cell_data['source'] = answer_data.answer
            resulting_notebook_content['cells'].append(answer_cell_data)

    return resulting_notebook_content

def generate_notebook_from_answer_list(notebook_data, answers):
    print('Generating answer notebook from answer list...')
    resulting_notebook_content = dict()
    resulting_notebook_content['metadata'] = notebook_data['metadata']
    resulting_notebook_content['nbformat'] = notebook_data['nbformat']
    resulting_notebook_content['nbformat_minor'] = notebook_data['nbformat_minor']
    resulting_notebook_content['cells'] = list()

    for answer_data in answers:
        answer_cell_data = dict()
        answer_cell_data['cell_type'] = answer_data.cell_type
        if answer_data.cell_type == 'code':
            answer_cell_data['outputs'] = answer_data.cell_outputs
            answer_cell_data['execution_count'] = None
        answer_cell_data['metadata'] = dict()
        answer_cell_data['source'] = answer_data.answer
        resulting_notebook_content['cells'].append(answer_cell_data)

    return resulting_notebook_content

if __name__ == '__main__':
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print_usage()
    else:
        notebook_path = sys.argv[1]
        resulting_notebook_path = sys.argv[2]
        answer_symbol = None
        if len(sys.argv) == 4:
            answer_symbol = sys.argv[3]

        notebook_data = dict()
        with open(notebook_path, 'r') as input_file:
            notebook_data = json.loads(input_file.read())

        # we extract the group names of the notebook cells
        cells = notebook_data['cells']
        group_names = list()
        for cell in notebook_data['cells']:
            if 'group' in cell['metadata'] and cell['metadata']['group'] not in group_names:
                group_names.append(cell['metadata']['group'])

        # we extract the answers from the notebook
        print('Extracting answers...')
        answers = None
        if len(group_names) > 1:
            answers = dict()
            for group in group_names:
                answers[group] = extract_group_answer(group, cells)
        elif len(group_names) == 1:
            group = group_names[0]
            answers = extract_answers_from_alternating_cells(group, cells)
        else:
            answers = extract_answers_from_marked_cells(cells, answer_symbol)

        # we generate a new notebook from the extracted answers
        print('Generating answer notebook...')
        if type(answers).__name__ == 'dict':
            resulting_notebook_content = generate_notebook_from_answer_dict(notebook_data, answers)
        else:
            resulting_notebook_content = generate_notebook_from_answer_list(notebook_data, answers)

        # we save the extracted answers to a notebook
        with open(resulting_notebook_path, 'w') as output_file:
            json.dump(resulting_notebook_content, output_file, indent=4)
        print('Answers extracted and saved under %s' % resulting_notebook_path)
