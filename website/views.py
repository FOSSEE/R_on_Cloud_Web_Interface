from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader, Context, Template
import requests
import uuid
from R_on_Cloud.config import (API_URL_UPLOAD, API_URL_RESET, AUTH_KEY,
                               API_URL_SERVER, URL)
from website.models import *
from django.db.models import Q
import json as simplejson
from . import utils
from django.db import connections
from collections import defaultdict
from .query import *
import pysolr
import json


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def catg():
    with connections['r'].cursor() as cursor:
        cursor.execute(GET_ALLMAINCATEGORY_SQL)
        category = dictfetchall(cursor)
    return category


def get_subcategories(maincat_id):
    with connections['r'].cursor() as cursor:
        cursor.execute(GET_SUBCATEGORY_SQL,
                       params=[maincat_id])
        subcategories = dictfetchall(cursor)
    return subcategories


def get_books(category_id):

    with connections['r'].cursor() as cursor:
        cursor.execute(GET_TBC_PREFERENCE_FROM_CATEGORY_ID_SQL,
                       params=[category_id])
        books = dictfetchall(cursor)
    return books


def get_chapters(book_id):
    with connections['r'].cursor() as cursor:
        cursor.execute(GET_TBC_CHAPTER_SQL,
                       params=[book_id])
        chapters = dictfetchall(cursor)

    return chapters


def get_examples(chapter_id):
    with connections['r'].cursor() as cursor:
        cursor.execute(GET_TBC_EXAMPLE_SQL,
                       params=[chapter_id])
        examples = dictfetchall(cursor)
    return examples


def get_revisions(example_id):
    with connections['r'].cursor() as cursor:
        cursor.execute(GET_TBC_EXAMPLE_FILE_SQL, params=[example_id])
        example_file = cursor.fetchone()
    example_file_filepath = example_file[4] + '/' + example_file[5]
    commits = utils.get_commits(file_path=example_file_filepath)
    return commits


def get_code(file_path, commit_sha):

    code = utils.get_file(file_path, commit_sha, main_repo=True)
    return code


def index(request):
    context = {}
    user_id = uuid.uuid4()
    context['api_url_upload'] = API_URL_UPLOAD
    context['reset_req_url'] = API_URL_RESET
    context['api_url'] = API_URL_SERVER
    book_id = request.GET.get('book_id')
    user = request.user
    if not 'user_id' in request.session:
        request.session['user_id'] = str(user_id)

    if not (request.GET.get('eid') or request.GET.get('book_id')):
        catg_all = catg()

        if 'maincat_id' in request.session:
            maincat_id = request.session['maincat_id']
            context['maincat_id'] = int(maincat_id)
            context['subcatg'] = get_subcategories(maincat_id)

        if 'subcategory_id' in request.session:
            category_id = request.session['subcategory_id']
            context['subcategory_id'] = int(category_id)
            context['books'] = get_books(category_id)

        if 'book_id' in request.session:
            book_id = request.session['book_id']
            context['book_id'] = int(book_id)
            context['chapters'] = get_chapters(book_id)

        if 'chapter_id' in request.session:
            chapter_id = request.session['chapter_id']
            context['chapter_id'] = int(chapter_id)
            context['examples'] = get_examples(chapter_id)

        if 'example_id' in request.session:
            example_id = request.session['example_id']
            context['eid'] = int(example_id)
            context['revisions'] = get_revisions(example_id)
            with connections['r'].cursor() as cursor:
                cursor.execute(GET_TBC_EXAMPLE_R_CLOUD_COMMENT_SQL,
                               params=[example_id])
                review = cursor.fetchone()
            review_url = "https://r.fossee.in/cloud_comments/" + \
                str(example_id)
            context['review'] = review[0]
            context['review_url'] = review_url

        if 'commit_sha' in request.session:
            commit_sha = request.session['commit_sha']
            context['commit_sha'] = commit_sha

            if 'code' in request.session:
                session_code = request.session['code']
                context['code'] = session_code
            elif 'filepath' in request.session:
                session_code = get_code(
                    request.session['filepath'], commit_sha)
                context['code'] = session_code
        context = {
            'catg': catg_all,
            'api_url_upload': API_URL_UPLOAD,
            'user_id': request.session['user_id'],
            'key': AUTH_KEY,
            'api_url': API_URL_SERVER,
        }
        template = loader.get_template('index.html')
        return HttpResponse(template.render(context, request))
    elif book_id:
        with connections['r'].cursor() as cursor:
            cursor.execute(GET_BOOK_CATEGORY_FROM_ID,
                           params=[book_id])
            books = cursor.fetchone()
        books = list(books)

        if len(books) == 0:
            catg_all = catg(None, all_cat=True)
            context = {
                'catg': catg_all,
                'err_msg': """This book is not supported by Scilab on Cloud."""
                           """ You are redirected to home page."""
            }
            context['api_url_upload'] = API_URL_UPLOAD
            context['reset_req_url'] = API_URL_RESET
            context['api_url'] = API_URL_SERVER
            template = loader.get_template('index.html')
            return HttpResponse(template.render(context, request))

        req_books = get_books(books[2])
        maincat_id = books[0]
        subcat_id = books[2]
        request.session['maincat_id'] = maincat_id
        request.session['subcategory_id'] = subcat_id
        request.session['book_id'] = book_id
        chapters = get_chapters(book_id)
        subcateg_all = TextbookCompanionSubCategoryList.objects\
            .using('r').filter(maincategory_id=maincat_id)\
            .order_by('subcategory_id')
        categ_all = TextbookCompanionCategoryList.objects.using('r')\
            .filter(~Q(category_id=0)).order_by('maincategory')
        context = {
            'catg': categ_all,
            'subcatg': subcateg_all,
            'maincat_id': maincat_id,
            'chapters': chapters,
            'subcategory_id': books[2],
            'books': req_books,
            'book_id': int(book_id),

        }
        context['api_url_upload'] = API_URL_UPLOAD
        context['reset_req_url'] = API_URL_RESET
        template = loader.get_template('index.html')
        return HttpResponse(template.render(context, request))
    else:
        try:
            eid = int(request.GET['eid'])
        except ValueError:
            context = {
                'catg': catg_all,
                'err_msg': """This example is currently not available on """
                           """scilab on cloud."""
            }
            context['api_url_upload'] = API_URL_UPLOAD
            context['reset_req_url'] = API_URL_RESET
            context['api_url'] = API_URL_SERVER
            template = loader.get_template('index.html')
            return HttpResponse(template.render(context, request))

        if eid:
            try:
                with connections['r'].cursor() as cursor:
                    cursor.execute(GET_TBC_EXAMPLE_R_CLOUD_COMMENT_SQL,
                                   params=[eid])

                    review = cursor.fetchone()
                review_url = "https://r.fossee.in/cloud_comments/" + str(eid)

                with connections['r'].cursor() as cursor:
                    cursor.execute(GET_TBC_EXAMPLE_CHAPTER_ID_SQL,
                                   params=[eid])

                    chapter_id = cursor.fetchone()

                with connections['r'].cursor() as cursor:
                    cursor.execute(GET_TBC_CHAPTER_DETAIL_SQL,
                                   params=[chapter_id[0]])
                    chapters = dictfetchall(cursor)

                with connections['r'].cursor() as cursor:
                    cursor.execute(GET_TBC_CHAPTER_PREFERENCE_ID_SQL,
                                   params=[chapter_id[0]])
                    preference_id = cursor.fetchone()
                with connections['r'].cursor() as cursor:
                    rows_count = cursor.execute(GET_TBC_PREFERENCE_DETAIL_CATEGORY_SQL,
                                                params=[preference_id[0]])
                    if rows_count > 0:
                        books_detail = cursor.fetchone()
                        books = get_books(books_detail[1])
                        maincat_id = books_detail[0]
                        subcat_id = books_detail[1]
                    else:
                        catg_all = catg()
                        context = {
                            'catg': catg_all,
                            'err_msg': """This book is not supported by R on Cloud."""
                            """ You are redirected to home page."""
                        }
                        context['api_url_upload'] = API_URL_UPLOAD
                        context['reset_req_url'] = API_URL_RESET
                        context['api_url'] = API_URL_SERVER
                        template = loader.get_template('index.html')
                        return HttpResponse(template.render(context, request))

                with connections['r'].cursor() as cursor:
                    cursor.execute(GET_TBC_EXAMPLE_FILE_SQL,
                                   params=[eid])

                with connections['r'].cursor() as cursor:
                    cursor.execute(GET_TBC_EXAMPLE_FILE_SQL,
                                   params=[eid])

                    example_file = cursor.fetchone()
                example_file_filepath = example_file[4] + '/' + example_file[5]
                with connections['r'].cursor() as cursor:
                    cursor.execute(GET_TBC_EXAMPLE_VIEW_SQL,
                                   params=[eid])
                    ex_views_count = cursor.fetchone()

                request.session['maincat_id'] = maincat_id
                request.session['subcategory_id'] = subcat_id
                request.session['book_id'] = preference_id[0]
                request.session['chapter_id'] = chapter_id[0]
                request.session['example_id'] = eid
                request.session['example_file_id'] = example_file[3]
                request.session['filepath'] = example_file_filepath

                revisions = get_revisions(eid)
                code = get_code(example_file_filepath, revisions[0][1])
                request.session['commit_sha'] = revisions[0][1]

            except IndexError:
                categ_all = TextbookCompanionCategoryList.objects\
                    .using('r').filter(~Q(category_id=0))\
                    .order_by('maincategory')
                context = {
                    'catg': categ_all,
                    'err_msg': """This example is currently not available on"""
                               """ scilab on cloud."""
                }
                context['api_url_upload'] = API_URL_UPLOAD
                context['api_url'] = API_URL_SERVER
                template = loader.get_template('index.html')
                return HttpResponse(template.render(context, request))
            subcateg_all = get_subcategories(maincat_id)
            categ_all = catg()
            if ex_views_count != None:
                if len(list([ex_views_count[0]])) != 0:
                    ex_views_count = ex_views_count[0]
                else:
                    ex_views_count = 0
            else:
                ex_views_count = 0
            context = {
                'catg': categ_all,
                'subcatg': subcateg_all,
                'maincat_id': maincat_id,
                'subcategory_id': subcat_id,
                'books': list(books),
                'book_id': preference_id[0],
                'chapters': chapters,
                'chapter_id': chapter_id[0],
                'examples': get_examples(chapter_id[0]),
                'eid': eid,
                'revisions': revisions,
                'commit_sha': revisions[0][1],
                'code': code,
                'ex_views_count': ex_views_count,
                'review': review[0],
                'review_url': review_url,
            }

            # if not user.is_anonymous():
            #    context['user'] = user
            context['api_url_upload'] = API_URL_UPLOAD
            context['reset_req_url'] = API_URL_RESET
            context['api_url'] = API_URL_SERVER
            template = loader.get_template('index.html')
            return HttpResponse(template.render(context, request))


def update_view_count(request):
    ex_id = request.GET.get('ex_id')
    with connections['r'].cursor() as cursor:
        cursor.execute(GET_TBC_CHAPTER_ID_SQL, params=[ex_id])
        Example_chapter_id = cursor.fetchone()
    with connections['r'].cursor() as cursor:
        cursor.execute(INSERT_TBC_EXAMPLE_VIEW_SQL,
                       params=[ex_id, Example_chapter_id[0]])
    with connections['r'].cursor() as cursor:
        cursor.execute(UPDATE_TBC_EXAMPLE_VIEW_SQL,
                       params=[ex_id])
    with connections['r'].cursor() as cursor:
        cursor.execute(GET_TBC_EXAMPLE_VIEW_SQL,
                       params=[ex_id])
        Example_views_count = cursor.fetchone()
    data = Example_views_count[0]
    return HttpResponse(simplejson.dumps(data),
                        content_type='application/json')


def reset(request):
    try:
        for key, value in list(request.session.items()):
            if key != 'user_id':
                del request.session[key]
            response = {"data": "ok"}
            return HttpResponse(simplejson.dumps(response),
                                content_type='application/json')
    except KeyError:
        pass
    response = {"data": "ok"}
    return HttpResponse(simplejson.dumps(response),
                        content_type='application/json')


def search_book(request):
    result = {}
    response_dict = []
    if request.is_ajax():
        exact_search_string = request.GET.get('search_string')
        search_string = "%" + exact_search_string + "%"
        with connections['r'].cursor() as cursor:
            cursor.execute(GET_SEARCH_BOOK_SQL, [search_string, search_string,
                                                 str(exact_search_string),
                                                 str(exact_search_string)])
            result = dictfetchall(cursor)
    return HttpResponse(simplejson.dumps(result),
                        content_type='application/json')


def popular(request):
    result = {}
    response_dict = []
    if request.is_ajax():
        search_string = request.GET.get('search_string')
        search_string = "%" + search_string + "%"
        with connections['r'].cursor() as cursor:
            cursor.execute(GET_SEARCH_POPULAR_BOOK_SQL)
            result = dictfetchall(cursor)
    return HttpResponse(simplejson.dumps(result),
                        content_type='application/json')


def recent(request):
    result = {}
    response_dict = []
    if request.is_ajax():
        exact_search_string = request.GET.get('search_string')
        search_string = "%" + exact_search_string + "%"
        with connections['r'].cursor() as cursor:
            cursor.execute(GET_SEARCH_RECENT_BOOK_SQL)
            result = dictfetchall(cursor)
    return HttpResponse(simplejson.dumps(result),
                        content_type='application/json')


def update_pref_hits(pref_id):
    updatecount = TextbookCompanionPreferenceHits.objects.using('r')\
        .filter(pref_id=pref_id)\
        .update(hitcount=F('hitcount') + 1)
    if not updatecount:
        insertcount = TextbookCompanionPreferenceHits.objects.using('r')\
            .get_or_create(pref_id=pref_id, hitcount=1)
    return


def solr_search_string(request):

    try:
        requests.get(URL)
        results = {}
        context = []
        response_dict = []
        search_string = request.GET.get('search_string')
        q = "content:'{0}'".format(search_string)
        fl = "*"
        qt = "select"
        fq = "*"
        rows = "100"
        wt = 'json'
        solr = pysolr.Solr(URL, search_handler="/"+qt, timeout=5)
        results = solr.search(q, **{
            'rows': rows,
            'group': 'true',
            'group.field': 'example',
            'group.limit': '1',
            'group.main': 'true',
        })
        for obj in results:
            response = {
                'example_id': obj['id'],
                'book_id': obj['book_id'],
                'book': obj['title'],
                'author': obj['author'],
                'chapter': obj['chapter'],
                'example': obj['example'],
            }
            response_dict.append(response)

        print("Saw {0} result(s).".format(len(results)))
        template = loader.get_template('search_code.html')
        context = {'data': response_dict}
        data = template.render(context)
        return JsonResponse({'data': data})
    except Exception:
        context = {'data': ''}
        template = loader.get_template('search_code.html')
        data = template.render(context)
        return JsonResponse({'data': '', 'error': 'True'})


def checkserver(request):
    try:
        req_status = requests.get(API_URL_SERVER)
        return JsonResponse({'status': req_status.status_code})
    except Exception:
        return JsonResponse({'error': 'True'})
