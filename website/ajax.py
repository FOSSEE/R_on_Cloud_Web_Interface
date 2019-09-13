from django.forms.models import model_to_dict
import json as simplejson
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core import serializers

# from django.http import HttpResponse, HttpResponseRedirect
# from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.context_processors import csrf
# from django.utils.html import strip_tags
from django.template.loader import render_to_string, get_template
from django.views.decorators.csrf import csrf_exempt, csrf_protect

# from django.db.models import Q
from textwrap import dedent
from R_on_Cloud.config import FROM_EMAIL, TO_EMAIL, CC_EMAIL, BCC_EMAIL
from website.views import catg, dictfetchall
from website.models import *
from website.forms import BugForm, RevisionForm, issues

from . import utils
from .query import *

import base64
from django.db import connections


def remove_from_session(request, keys):
    for key in keys:
        request.session.pop(key, None)


def subcategories(request):
    context = {}
    response_dict = []
    if request.is_ajax():
        maincategory_id = int(request.GET.get('maincat_id'))
        if maincategory_id:
            request.session['maincat_id'] = maincategory_id
            with connections['r'].cursor() as cursor:
                cursor.execute(GET_SUBCATEGORY_SQL, params=[maincategory_id])
                subcategory = cursor.fetchall()
            for obj in subcategory:
                response = {
                    'subcategory_id': obj[1],
                    'subcategory': obj[2],
                }
                response_dict.append(response)
            return HttpResponse(simplejson.dumps(response_dict),
                                content_type='application/json')


def books(request):
    context = {}
    response_dict = []
    if request.is_ajax():
        main_category_id = int(request.GET.get('maincat_id'))
        category_id = int(request.GET.get('cat_id'))

        if category_id:
            # store category_id in cookie/session
            request.session['subcategory_id'] = category_id
            request.session['maincat_id'] = main_category_id
            remove_from_session(request, [
                'book_id',
                'chapter_id',
                'example_id',
                'commit_sha',
                'example_file_id',
                'filepath',
                'code',
            ])

            with connections['r'].cursor() as cursor:
                cursor.execute(GET_TBC_PREFERENCE_SQL,
                               params=[main_category_id, category_id])
                books = cursor.fetchall()
            for obj in books:
                response = {
                    'id': obj[1],
                    'book': obj[4],
                    'author': obj[5]
                }

                response_dict.append(response)
            return HttpResponse(simplejson.dumps(response_dict),
                                content_type='application/json')


def chapters(request):
    context = {}
    response_dict = []
    if request.is_ajax():
        book_id = int(request.GET.get('book_id'))
        if book_id:
            request.session['book_id'] = book_id
            remove_from_session(request, [
                'chapter_id',
                'example_id',
                'commit_sha',
                'example_file_id',
                'filepath',
                'code',
            ])

            with connections['r'].cursor() as cursor:
                cursor.execute(GET_TBC_CHAPTER_SQL, params=[book_id])
                chapters = cursor.fetchall()
            for obj in chapters:
                response = {
                    'id': obj[0],
                    'number': obj[1],
                    'chapter': obj[2],

                }
                response_dict.append(response)
            return HttpResponse(simplejson.dumps(response_dict),
                                content_type='application/json')


def examples(request):
    context = {}
    response_dict = []
    if request.is_ajax():
        chapter_id = int(request.GET.get('chapter_id'))
        if chapter_id:
            request.session['chapter_id'] = chapter_id
            remove_from_session(request, [
                'example_id',
                'commit_sha',
                'example_file_id',
                'filepath',
                'code',
            ])

            with connections['r'].cursor() as cursor:
                cursor.execute(GET_TBC_EXAMPLE_SQL, params=[chapter_id])
                examples = cursor.fetchall()
            for obj in examples:
                response = {
                    'id': obj[0],
                    'number': obj[1],
                    'caption': obj[2],
                }
                response_dict.append(response)
            return HttpResponse(simplejson.dumps(response_dict),
                                content_type='application/json')


def revisions(request):
    commits = {}
    response_dict = []
    if request.is_ajax():
        example_id = int(request.GET.get('example_id'))
        request.session['example_id'] = example_id
        remove_from_session(request, [
            'commit_sha',
            'example_file_id',
            'filepath',
            'code',
        ])

        with connections['r'].cursor() as cursor:
            cursor.execute(GET_TBC_EXAMPLE_FILE_SQL, params=[example_id])
            example_file = cursor.fetchone()
        example_file_filepath = example_file[4] + '/' + example_file[5]
        request.session['example_file_id'] = example_file[3]
        request.session['filepath'] = example_file_filepath
        commits = utils.get_commits(file_path=example_file_filepath)
        response = {
            'commits': commits,
        }
        response_dict.append(response)
        return HttpResponse(simplejson.dumps(response),
                            content_type='application/json')


def code(request):
    commits = {}
    response_dict = []
    if request.is_ajax():
        commit_sha = request.GET.get('commit_sha')
        request.session['commit_sha'] = commit_sha
        remove_from_session(request, [
            'code',
        ])
        code = ''
        review = ''
        review_url = ''
        example_id = request.session['example_id']
        if not example_id:
            example_id = int(request.GET.get('example_id'))
        file_path = request.session['filepath']
        #review = ScilabCloudComment.objects.using('r')\
        #    .filter(example=example_id).count()
        review = 0
        with connections['r'].cursor() as cursor:
            cursor.execute(GET_TBC_EXAMPLE_VIEW_SQL, params=[example_id])
            exmple = cursor.fetchone()
        review_url = "https://scilab.in/cloud_comments/" + str(example_id)

        file = utils.get_file(file_path, commit_sha, main_repo=True)
        code = file
        response = {
            'code': code,
            'review': review,
            'review_url': review_url,
            'exmple': exmple[0]
        }
        # response_dict.append(response)
        return HttpResponse(simplejson.dumps(response),
                            content_type='application/json')


def contributor(request):
    context = {}
    contributor = {}
    response_dict = []
    if request.is_ajax():
        book_id = int(request.GET.get('book_id'))

        with connections['r'].cursor() as cursor:
            cursor.execute(GET_TBC_CONTRIBUTOR_DETAILS_SQL, params=[book_id])
            contributor = cursor.fetchone()
        response = {
            "contributor_name": contributor[1],
            "proposal_faculty": contributor[2],
            "proposal_reviewer": contributor[3],
            "proposal_university": contributor[4],
        }
        response_dict.append(response)
    return HttpResponse(simplejson.dumps(response),
                        content_type='application/json')


def node(request):
    context = {}
    response_dict = []
    if request.is_ajax():
        key = request.GET.get('key')
        response = render_to_string(
            "node-{0}.html".format(key))
        return HttpResponse(simplejson.dumps(response),
                            content_type='application/json')


def bug_form(request):
    context = {}
    response_dict = []
    if request.is_ajax():
        bug_form = request.GET.get('bug_form')
        form = BugForm()
        context['form'] = BugForm()
        context.update(csrf(request))
        response = render_to_string('bug-form.html', context)
        return HttpResponse(simplejson.dumps(response),
                            content_type='application/json')


def bug_form_submit(request):
    context = {}
    response_dict = []
    if request.is_ajax():
        form = request.GET.get('form')
        cat_id = request.GET.get('cat_id')
        book_id = request.GET.get('book_id')
        chapter_id = request.GET.get('chapter_id')
        ex_id = request.GET.get('ex_id')
        if form.is_valid():
            comment = form.cleaned_data['description']
            error = form.cleaned_data['issue']
            email = form.cleaned_data['email']
            comment_data = TextbookCompanionPreference.objects\
                .db_manager('r').raw(dedent("""\
                    SELECT 1 as id, tcp.book as book, tcp.author as author,
                    tcp.publisher as publisher, tcp.year as year,
                    tcp.category as category, tce.chapter_id,
                    tcc.number AS chapter_no, tcc.name AS chapter_name,
                    tce.number AS example_no, tce.caption AS example_caption
                    FROM textbook_companion_preference tcp
                    LEFT JOIN textbook_companion_chapter tcc ON
                    tcp.id = tcc.preference_id 
                    LEFT JOIN textbook_companion_example
                    tce ON tce.chapter_id = tcc.id WHERE tce.id = %s"""),
                                     [ex_id])
            book_name = comment_data[0].book
            book_author = comment_data[0].author
            book_publisher = comment_data[0].publisher
            chapter_number = comment_data[0].chapter_no
            chapter_name = comment_data[0].chapter_name
            example_number = comment_data[0].example_no
            example_caption = comment_data[0].example_caption
            all_cat = False
            category = catg(comment_data[0].category, all_cat)
            subcategory = 0
            error_int = int(error)
            error = issues[error_int][1]
            context = {
                'category': category,
                'subcategory': subcategory,
                'error': error,
                'book': book_name,
                'author':  book_author,
                'publisher': book_publisher,
                'chapter_name': chapter_name,
                'chapter_no': chapter_number,
                'example_id': ex_id,
                'example_caption': example_caption,
                'example_no': example_number,
                'comment': comment,
            }
            scilab_comment = ScilabCloudComment()
            scilab_comment.type = error_int
            scilab_comment.comment = comment
            scilab_comment.email = email
            scilab_comment.category = comment_data[0].category
            scilab_comment.books = book_id
            scilab_comment.chapter = chapter_id
            scilab_comment.example = ex_id
            scilab_comment.save(using='r')
            subject = "New Cloud Comment"
            message = render_to_string('email.html', context)
            from_email = FROM_EMAIL
            to_email = TO_EMAIL
            cc_email = CC_EMAIL
            bcc_email = BCC_EMAIL
            # Send Emails to, cc, bcc
            msg = EmailMultiAlternatives(
                subject,
                message,
                from_email,
                [to_email],
                bcc=[bcc_email],
                cc=[cc_email]
            )
            msg.content_subtype = "html"
            msg.send()
            response = "Thank you for your feedback"
            return HttpResponse(simplejson.dumps(response),
                                content_type='application/json')
# submit revision


def revision_form(request):

    context = {}
    response_dict = []
    if request.is_ajax():
        code = request.GET.get('code')
        code = code.decode('UTF-8')
        initial_code = request.GET.get('initial_code')
        request.session['code'] = code.decode('UTF-8')

        if code == initial_code:
            response = "You have not made any changes"
            return HttpResponse(simplejson.dumps(response),
                                content_type='application/json')

        if not request.user.is_anonymous():
            if 'commit_sha' not in request.session:
                response = "Please select a revision"
                return HttpResponse(simplejson.dumps(response),
                                    content_type='application/json')

            form = RevisionForm()
            context = {'form': form}
            context.update(csrf(request))
            response = render_to_string(
                'submit-revision.html', context)
            return HttpResponse(simplejson.dumps(response),
                                content_type='application/json')
        else:
            response = render_to_string(
                'revision-login.html', {})
        return HttpResponse(simplejson.dumps(response),
                            content_type='application/json')


# @dajaxice_register
def revision_error(request):
    context = {
        'error_message': 'You have not made any changes',
    }
    response = render_to_string(
        'submit-revision-error.html', context)
    return HttpResponse(simplejson.dumps(response),
                        content_type='application/json')


def revision_form_submit(request):
    if request.is_ajax():
        form = request.GET.get('form')
        code = request.GET.get('code')
        code = code.decode('UTF-8')

        form = RevisionForm(deserialize_form(form))

        if form.is_valid():

            commit_message = form.cleaned_data['commit_message']
            username, email = request.user.username, request.user.email

            # push changes to temp repo
            # update_file returns True if the push is success.
            commit_sha = utils.update_file(
                request.session['filepath'],
                commit_message,
                base64.b64encode(code),
                [username, email],
                main_repo=False,
            )

            if commit_sha is not None:
                # everything is fine

                # save the revision info in database
                rev = TextbookCompanionRevision(
                    example_file_id=request.session['example_file_id'],
                    commit_sha=commit_sha,
                    commit_message=commit_message,
                    committer_name=username,
                    committer_email=email,
                )
                rev.save(using='r')

                response = 'submitted successfully! \nYour changes will be'
                'visible after review.'
                return HttpResponse(simplejson.dumps(response),
                                    content_type='application/json')
        else:
            response = 'Some error occures.'
            return HttpResponse(simplejson.dumps(response),
                                content_type='application/json')


def diff(request):
    if request.is_ajax():
        diff_commit_sha = request.GET.get('diff_commit_sha')
        editor_code = request.GET.get('editor_code')
    context = {}
    file_path = request.session['filepath']
    file = utils.get_file(file_path, diff_commit_sha, main_repo=True)
    code = file
    response = {
        'code2': code,
    }
    return HttpResponse(simplejson.dumps(response),
                        content_type='application/json')

# ------------------------------------------------------------
# review interface functions


def review_revision(request):
    if request.is_ajax():
        revision_id = request.GET.get('revision_id')
        revision = TextbookCompanionRevision.objects.using(
            'r').get(id=revision_id)
        file = utils.get_file(revision.example_file.filepath,
                              revision.commit_sha, main_repo=False)
        code = base64.b64decode(file['content'])

        request.session['revision_id'] = revision_id

        example = revision.example_file.example
        chapter = example.chapter
        book = chapter.preference
        category = utils.get_category(book.category)

        response = {
            'code': code.decode('UTF-8'),
            'revision': model_to_dict(revision),
            'example': model_to_dict(example),
            'chapter': model_to_dict(chapter),
            'book': model_to_dict(book),
            'category': category,
            'createdAt': str(revision.timestamp),
        }
        return HttpResponse(simplejson.dumps(response),
                            content_type='application/json')


def push_revision(request):
    """
    code: from code editor on review interface
    """
    if request.is_ajax():
        code = request.GET.get('code')
        code = code.decode('UTF-8')
        revision = TextbookCompanionRevision.objects.using(
            'r').get(id=request.session['revision_id'])
        utils.update_file(
            revision.example_file.filepath,
            revision.commit_message,
            base64.b64encode(code.decode('UTF-8')),
            [revision.committer_name, revision.committer_email],
            branch='master',
            main_repo=True)
        revision.push_status = True
        revision.save()

        response = 'pushed successfully!'

        return HttpResponse(simplejson.dumps(response),
                            content_type='application/json')


def remove_revision(request):
    """
    remove revision from revision database
    """
    TextbookCompanionRevision.objects.using('r').get(
        id=request.session['revision_id']).delete()

    response = 'removed successfully!'
    return HttpResponse(simplejson.dumps(response),
                        content_type='application/json')
