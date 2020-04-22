# Generated by Django 3.0.4 on 2020-04-22 09:51

from django.db import transaction
from dataedit.models import Table
from api.actions import has_table
from api.actions import _get_engine
from dataedit.views import schema_whitelist
from sqlalchemy import inspect
from django.core.management.base import BaseCommand
from oeplatform.settings import PLAYGROUNDS

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check whether the databases line up, report possible mismatch',
        )

    def handle(self, *args, **options):
        check = options.get("check", False)
        migrate(check)

def migrate(check=True, verbose=True):
    def vprint(x):
        if verbose:
            print(x)
        else:
            return
    result = False
    if not check:
        answer = None
        while answer != "y":
            answer = input(
                "Warning! This opperation may alter your database. Continue only if you know possible implications! Continue (y/n)")
            if answer == "n":
                return False
    try:
        db_not_model = []
        with transaction.atomic():
            for table in Table.objects.all():
                if table.schema.name not in PLAYGROUNDS:
                    if not has_table(dict(schema=table.schema.name, table=table.name)):

                        if not check:
                            table.delete()
            if db_not_model:
                vprint("In model but not in database:")
                for t in db_not_model:
                    vprint(t)
            else:
                vprint("All models correspond to database tables :)")

            model_not_db = []
            engine = _get_engine()
            insp = inspect(engine)
            for schema in insp.get_schema_names():
                if schema in schema_whitelist and schema not in PLAYGROUNDS:
                    for table in insp.get_table_names(schema=schema):
                        try:
                            Table.objects.get(name=table, schema__name=schema)
                        except Table.DoesNotExist:
                            model_not_db.append((table.schema.name, table.name))
                            if not check:
                                table = Table.load(schema, table)
                                table.save()

            if model_not_db:
                vprint("In database but not in model:")
                for t in db_not_model:
                    vprint(t)
            else:
                vprint("All tables are reflected by models :)")
                if not db_not_model:
                    result = True

    except:
        print("An error occured during the migration of metadata")
        raise

    return result