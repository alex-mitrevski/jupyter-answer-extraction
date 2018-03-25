class Answer(object):
    def __init__(self, question_id='',
                 answer='', cell_type='markdown',
                 cell_outputs=list()):
        self.question_id = question_id
        self.answer = answer
        self.cell_type = cell_type
        self.cell_outputs = cell_outputs
