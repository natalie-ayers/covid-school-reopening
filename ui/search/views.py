import json
import traceback
import sys
import csv
import os

from functools import reduce
from operator import and_

from django.shortcuts import render
from django import forms

from query_schools import query_results

NOPREF_STR = 'No preference'
RES_DIR = os.path.join(os.path.dirname(__file__), '..', 'res')
COLUMN_NAMES = dict(
    school='School',
    community='Community',
    city='City',
    attendance="% Attendance 2019",
    broadband="% Children with Broadband",
    covid="Average Monthly Covid Positivity Rate",
    grade_level="Grade Level"
)


def _valid_result(res):
    """Validate results returned by query_results."""
    (HEADER, RESULTS) = [0, 1]
    ok = (isinstance(res, list))
    ok = (isinstance(res, (tuple, list)) and
          len(res) == 2 and
          isinstance(res[HEADER], (tuple, list)) and
          isinstance(res[RESULTS], (tuple, list)))
    if not ok:
        return False

    n = len(res[HEADER])

    def _valid_row(row):
        return isinstance(row, (tuple, list)) and len(row) == n
    return reduce(and_, (_valid_row(x) for x in res[RESULTS]), True)


def _load_column(filename, col=0):
    """Load single column from csv file."""
    with open(filename) as f:
        col = list(zip(*csv.reader(f)))[0]
        return list(col)


def _load_res_column(filename, col=0):
    """Load column from resource directory."""
    return _load_column(os.path.join(RES_DIR, filename), col=col)


def _build_dropdown(options):
    """Convert a list to (value, caption) tuples."""
    return [(x, x) if x is not None else ('', NOPREF_STR) for x in options]

NEIGHBORHOOD = _build_dropdown([None] + _load_res_column('nbhd_list.csv'))
CITY = _build_dropdown(_load_res_column('city_list.csv'))
MONTH = _build_dropdown(_load_res_column('month_list.csv'))
GRADE = _build_dropdown(_load_res_column('grade_list.csv'))
SORT = _build_dropdown(_load_res_column('columns.csv'))


class SearchForm(forms.Form):
    city = forms.ChoiceField(label='City', choices=CITY, required=False)
    neighborhood = forms.CharField(
        label='Community',
        help_text='e.g. HYDE PARK',
        required=False)
    school = forms.CharField(
        label="School",
        help_text='e.g. BRET HARTE ELEMENTARY SCHOOL',
        required=False)
    month = forms.ChoiceField(label='Month', choices=MONTH, required=False)
    grade_level = forms.ChoiceField(label='Grade Level', choices=GRADE, required=False)
    sort_by = forms.ChoiceField(label='Sort (Descending)', choices=SORT, required=False)
    show_args = forms.BooleanField(label='Show args_to_ui',
                                   required=False)


def home(request):
    context = {}
    res = None
    if request.method == 'GET':
        form = SearchForm(request.GET)
        if form.is_valid():

            args = {}

            city = form.cleaned_data['city']
            if city:
                args['city'] = (city)

            neighborhood = form.cleaned_data['neighborhood']
            if neighborhood:
                args['neighborhood'] = neighborhood

            school = form.cleaned_data['school']
            if school:
                args['school'] = school

            month = form.cleaned_data['month']
            if month:
                args['month'] = month

            grade = form.cleaned_data['grade_level']
            if grade:
                args['grade_level'] = grade

            sort_by = form.cleaned_data['sort_by']
            if sort_by:
                args['sort_by'] = sort_by

            if form.cleaned_data['show_args']:
                context['args'] = 'args_to_ui = ' + json.dumps(args, indent=2)

            try:
                res = query_results(args)
            except Exception as e:
                print('Exception caught')
                bt = traceback.format_exception(*sys.exc_info()[:3])
                context['err'] = """
                An exception was thrown in query_results:
                <pre>{}
{}</pre>
                """.format(e, '\n'.join(bt))

                res = None
    else:
        form = SearchForm()

    # Handle different responses of res
    if res is None:
        context['result'] = None
    elif isinstance(res, str):
        context['result'] = None
        context['err'] = res
        result = None
    elif not _valid_result(res):
        context['result'] = None
        context['err'] = ('Return of query_results has the wrong data type. '
                          'Should be a tuple of length 4 with one string and '
                          'three lists.')
    else:
        columns, result = res

        # Wrap in tuple if result is not already
        if result and isinstance(result[0], str):
            result = [(r,) for r in result]

        context['result'] = result
        context['num_results'] = len(result)
        context['columns'] = [COLUMN_NAMES.get(col, col) for col in columns]

    context['form'] = form
    return render(request, 'index.html', context)
