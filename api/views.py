import json
import time

from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

import api.parser
from api import actions
from api import parser
from api.helpers.http import ModHttpResponse


class Table(View):
    """
    Handels the creation of tables and serves information on existing tables
    """

    def get(self, request, schema, table):
        """
        Returns a dictionary that describes the DDL-make-up of this table.
        Fields are:

        * name : Name of the table,
        * schema: Name of the schema,
        * columns : as specified in :meth:`api.actions.describe_columns`
        * indexes : as specified in :meth:`api.actions.describe_indexes`
        * constraints: as specified in
                    :meth:`api.actions.describe_constraints`

        :param request:
        :return:
        """
        return JsonResponse({
            'schema': schema,
            'name': table,
            'columns': actions.describe_columns(schema, table),
            'indexed': actions.describe_indexes(schema, table),
            'constraints': actions.describe_constraints(schema, table)
        })

    def post(self, request, schema, table):
        """
        Changes properties of tables and table columns
        :param request:
        :param schema:
        :param table:
        :return:
        """

        json_data = json.loads(request.body.decode("utf-8"))

        if 'column' in json_data['type']:

            column_definition = api.parser.parse_scolumnd_from_columnd(schema, table, json_data['name'], json_data)
            result = actions.queue_column_change(schema, table, column_definition)
            return ModHttpResponse(result)

        elif 'constraint' in json_data['type']:

            # Input has nothing to do with DDL from Postgres.
            # Input is completely different.
            # Using actions.parse_sconstd_from_constd is not applicable
            # dict.get() returns None, if key does not exist
            constraint_definition = {
                'action': json_data['action'],  # {ADD, DROP}
                'constraint_type': json_data.get('constraint_type'),  # {FOREIGN KEY, PRIMARY KEY, UNIQUE, CHECK}
                'constraint_name': json_data.get('constraint_name'),  # {myForeignKey, myUniqueConstraint}
                'constraint_parameter': json_data.get('constraint_parameter'),
                # Things in Brackets, e.g. name of column
                'reference_table': json_data.get('reference_table'),
                'reference_column': json_data.get('reference_column')
            }

            result = actions.queue_constraint_change(schema, table, constraint_definition)
            return ModHttpResponse(result)
        else:
            return ModHttpResponse(actions.get_response_dict(False, 400, 'type not recognised'))

    def put(self, request, schema, table):
        """
        Every request to unsave http methods have to contain a "csrftoken".
        This token is used to deny cross site reference forwarding.
        In every request the header had to contain "X-CSRFToken" with the actual csrftoken.
        The token can be requested at / and will be returned as cookie.

        :param request:
        :return:
        """

        # There must be a better way to do this.
        json_data = json.loads(request.body.decode("utf-8"))

        constraint_definitions = []
        column_definitions = []

        for constraint_definiton in json_data['constraints']:
            constraint_definiton.update({"action": "ADD",
                                         "c_table": table,
                                         "c_schema": schema})
            constraint_definitions.append(constraint_definiton)
        for column_definition in json_data['columns']:
            column_definition.update({"c_table": table,
                                      "c_schema": schema})
            column_definitions.append(column_definition)

        result = actions.table_create(schema, table, column_definitions, constraint_definitions)

        return ModHttpResponse(result)


class Index(View):
    def get(self, request):
        pass

    def post(self, request):
        pass

    def put(self, request):
        pass


class Rows(View):
    def get(self, request, schema, table):

        columns = request.GET.get('columns')
        where = request.GET.get('where')
        orderby = request.GET.get('orderby')
        limit = request.GET.get('limit')
        offset = request.GET.get('offset')

        data = {'schema': schema,
                'table': table,
                'columns': parser.split(columns, ','),
                'where': parser.split(parser.replace(where, "=", ","), ","),
                'orderby': parser.split(orderby, ','),
                'limit': limit,
                'offset': offset
                }

        return_obj = actions.get_rows(request, data)

        print(return_obj)
        # TODO: Figure out what JsonResponse does different.
        response = json.dumps(return_obj, default=date_handler)
        return HttpResponse(response, content_type='application/json')

    def post(self, request):
        pass

    def put(self, request):
        pass


class Session(View):
    def get(self, request, length=1):
        return request.session['resonse']


def date_handler(obj):
    """
    Implements a handler to serialize dates in JSON-strings
    :param obj: An object
    :return: The str method is called (which is the default serializer for JSON) unless the object has an attribute  *isoformat*
    """
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return str(obj)


# Create your views here.


def create_ajax_handler(func):
    """
    Implements a mapper from api pages to the corresponding functions in
    api/actions.py
    :param func: The name of the callable function
    :return: A JSON-Response that contains a dictionary with the corresponding response stored in *content*
    """

    @csrf_exempt
    def execute(request):
        content = request.POST if request.POST else request.GET
        data = func(json.loads(content['query']), {'user': request.user})

        # This must be done in order to clean the structure of non-serializable
        # objects (e.g. datetime)
        response_data = json.loads(json.dumps(data, default=date_handler))
        return JsonResponse({'content': response_data}, safe=False)

    return execute


def stream(data):
    """
    TODO: Implement streaming of large datasets
    :param data:
    :return:
    """
    size = len(data)
    chunck = 100

    for i in range(size):
        yield json.loads(json.dumps(data[i], default=date_handler))
        time.sleep(1)
