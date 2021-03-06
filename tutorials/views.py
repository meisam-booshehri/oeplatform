from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import exceptions, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from os.path import join

from uuid import uuid4

from copy import deepcopy

from django.conf import settings

from markdown2 import Markdown

from .forms import TutorialForm
from .models import Tutorial

import re
# Create your views here.

youtubeUrlRegex = re.compile('^.*youtube\.com\/watch\?v=(?P<id>[A-z0-9]+)$')

staticTutorials = [
    {
        "id": "e59819c7-46fd-4528-b2bd-f37e8866d1df",
        "title": "appBBB-UML.html",
        "fileName": "appBBB-UML.html"
    },
    {
        "id": "5064610a-596a-4911-8862-e9d815d872d4",
        "title": "df_normalize_denormalize.html",
        "fileName": "df_normalize_denormalize.html"
    },
    {
        "id": "56c675ea-93ae-43cf-886c-01f4fc98711f",
        "title": "germany-UML.html",
        "fileName": "germany-UML.html"
    },
    {
        "id": "7e51c992-5a8a-419f-b778-31a1dd32db4a",
        "title": "OEP-api_template.html",
        "fileName": "OEP-api_template.html"
    },
    {
        "id": "61201725-493f-4dd0-b9aa-6e0f6d6aa550",
        "title": "OEP_API_tutorial_part1.html",
        "fileName": "OEP_API_tutorial_part1.html"
    },
    {
        "id": "c4e48c2d-626a-45ad-aa68-a6711c7af85c",
        "title": "OEP_API_tutorial_part2.html",
        "fileName": "OEP_API_tutorial_part2.html"
    },
    {
        "id": "eab6aece-cff8-4265-989f-3dd9d7d03026",
        "title": "OEP_API_tutorial_part3.html",
        "fileName": "OEP_API_tutorial_part3.html"
    },
    {
        "id": "a1d6fc71-6694-4704-8ab4-950be4de9561",
        "title": "OEP_API_tutorial_part4.html",
        "fileName": "OEP_API_tutorial_part4.html"
    },
    {
        "id": "ea5e68ef-bcfb-47a1-9768-b5184797bcab",
        "title": "OEP-oedialect_eGoDP.html",
        "fileName": "OEP-oedialect_eGoDP.html"
    },
    {
        "id": "44634b85-389f-4c26-988f-217ee9c6f768",
        "title": "OEP-oedialect-geoquery.html",
        "fileName": "OEP-oedialect-geoquery.html"
    },
    {
        "id": "cc9e9a5e-826b-4296-a544-e057003dd22c",
        "title": "OEP-oedialect.html",
        "fileName": "OEP-oedialect.html"
    },
    {
        "id": "99f35e78-49ca-47f4-9926-d5197c0e3ffe",
        "title": "OEP-oedialect_template.html",
        "fileName": "OEP-oedialect_template.html"
    },
    {
        "id": "c254d5e4-479b-423f-92fb-c10411abab66",
        "title": "OEP-oedialect_upload_from_csv.html",
        "fileName": "OEP-oedialect_upload_from_csv.html"
    },
    {
        "id": "bc6ad0f4-d9ed-4f00-84e4-f3b62f3eafca",
        "title": "rli_tool_validate-metadata-datapackage.html",
        "fileName": "rli_tool_validate-metadata-datapackage.html"
    },
    {
        "id": "43d4da3a-4fef-4524-8c17-7214637e44ad",
        "title": "UML Tutorial.html",
        "fileName": "UML Tutorial.html"
    },
]


def _resolveStaticTutorial(tutorial):
    try:
        with open(join(settings.BASE_DIR, "examples", "build", tutorial["fileName"]), 'r') as buildFile:
                buildFileContent = buildFile.read()

        return {
            "html": buildFileContent
        }

    except:
        return {"html": "Tutorial is missing"}


def _resolveStaticTutorials(tutorials):
    resolvedTutorials = []

    # I was not able to solve this problem without an object spread operator due to my JS history.
    # The copy does not have a specific reason but not iterating over the array which is modified in interation.

    for tutorial in tutorials:
        paramsToAdd = _resolveStaticTutorial(tutorial)
        copiedTutorial = deepcopy(tutorial)
        copiedTutorial.update(paramsToAdd)

        resolvedTutorials.append(copiedTutorial)

    return resolvedTutorials


def _resolveDynamicTutorial(evaluatedQs):
    """


    :param evaluatedQs: Evaluated queryset object
    :return:
    """

    # Initialize dict that stores a tutorial
    currentTutorial = {'id': '', 'title': '', 'html': '', 'markdown': '', 'category': '', 'media_src': '', 'level': ''}

    # populate dict
    currentTutorial.update(id=str(evaluatedQs.id),
                           title=evaluatedQs.title,
                           html=evaluatedQs.html,
                           markdown=evaluatedQs.markdown,
                           category= evaluatedQs.category,
                           media_src= evaluatedQs.media_src,
                           level=evaluatedQs.level)

    return currentTutorial


def _resolveDynamicTutorials(tutorials_qs):
    """
    Evaluates a QuerySet and passes each evaluated object to the next function which returns a python
    dictionary that contains all parameters from the object as dict. The dict is added to a list to
    later merge the static and dynamic tutorials together.

    :param tutorials_qs:
    :return:
    """
    resolvedTutorials = []

    for tutorial in tutorials_qs:
        paramsToAdd = _resolveDynamicTutorial(tutorial)

        resolvedTutorials.append(paramsToAdd)

    return resolvedTutorials


def _gatherTutorials(id=None):
    """
    Collects all existing tutorials (static/dynamic) and returns them as a list. If an id is
    specified as parameter a specific tutorial is returned filtered by id.

    :param id:
    :return:
    """

    # Retrieve allTutorials objects from db and cache
    dynamicTutorialsQs = Tutorial.objects.all()

    tutorials = _resolveStaticTutorials(staticTutorials)
    tutorials.extend(_resolveDynamicTutorials(dynamicTutorialsQs))

    if id:
        filteredElement = list(filter(lambda tutorial: tutorial["id"] == id, tutorials))[0]
        return filteredElement

    return tutorials

def _processFormInput(form):
    tutorial = form.save(commit=False)
    # Add more information to the dataset like date, time, contributor ...

    if tutorial.media_src:
        matchResult = youtubeUrlRegex.match(tutorial.media_src)
        videoId = matchResult.group(1) if matchResult else None
        if videoId:
            tutorial.media_src = "https://www.youtube.com/embed/" + videoId

    return tutorial

def formattedMarkdown(markdown):
    """
    A parameter is used to enter a text formatted as markdown that is formatted
    to html and returned. This functionality is implemented using Markdown2.

    :param markdown:
    :return:
    """

    markdowner = Markdown(safe_mode="escape")

    return markdowner.convert(markdown)


class ListTutorials(View):
    def get(self, request):
        """
        Load and list the available tutorials.

        :param request: A HTTP-request object sent by the Django framework.
        :return: Tutorials renderer
        """

        # Gathering all tutorials

        tutorials = _gatherTutorials()

        return render(
            request, 'list.html', {"tutorials": tutorials}
        )


class TutorialDetail(View):
    def get(self, request, tutorial_id):
        """
        Detail view for specific tutorial.

        :param request: A HTTP-request object sent by the Django framework.
        :return: Tutorials renderer
        """

        # Gathering all tutorials

        tutorial = _gatherTutorials(tutorial_id)

        return render(
            request, 'detail.html', {"tutorial": tutorial}
        )


class CreateNewTutorial(LoginRequiredMixin, CreateView):
    template_name = 'add.html'
    redirect_url = 'detail_tutorial'
    form_class = TutorialForm
    login_url = '/user/login/'
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        """
         validates a form and stores the values in the database and inserts a
         value for the tutorials field html.

        :param form:
        :return:
        """

        tutorial = _processFormInput(form)
        tutorial.save()

        # Convert markdown to HTML and save to db
        _html = formattedMarkdown(tutorial.markdown)
        addHtml = Tutorial.objects.get(pk=tutorial.id)
        addHtml.html = _html
        addHtml.save()

        return redirect(self.redirect_url, tutorial_id=tutorial.id)

    def addTutorialFromMarkdownFile(self):
        pass


class EditTutorials(LoginRequiredMixin, UpdateView):
    template_name = 'add.html'
    redirect_url = 'detail_tutorial'
    model = Tutorial
    form_class = TutorialForm
    pk_url_kwarg = 'tutorial_id'
    login_url = '/user/login/'
    redirect_field_name = 'redirect_to'

    def form_valid(self, form):
        """
        validates a form and stores the values in the database and inserts a
         value for the tutorials field html.

        :param form:
        :return:
        """
        tutorial = _processFormInput(form)
        tutorial.save()

        _html = formattedMarkdown(tutorial.markdown)
        addHtml = Tutorial.objects.get(pk=tutorial.id)
        addHtml.html = _html
        addHtml.save()

        return redirect(self.redirect_url, tutorial_id=tutorial.id)


class DeleteTutorial(LoginRequiredMixin, DeleteView):
    template_name = 'tutorial_confirm_delete.html'
    model = Tutorial
    pk_url_kwarg = 'tutorial_id'
    success_url = reverse_lazy('list_tutorials')
    login_url = '/user/login/'
    redirect_field_name = 'redirect_to'








