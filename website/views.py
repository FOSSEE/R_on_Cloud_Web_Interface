from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
import requests
import uuid
from website.models import *
from django.db.models import Q
import json as simplejson
from . import utils
from django.db import connections
from .query import *


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def catg(cat_id, all_cat):
    if all_cat is False:
        category = TextbookCompanionCategoryList.objects.using('r')\
            .get(category_id=cat_id)
        return category.maincategory
    else:
        category = TextbookCompanionCategoryList.objects.using('r')\
            .filter(~Q(category_id=0)).order_by('maincategory')
        return category


def subcatg(subcat_id, all_subcat):
    if all_subcat is False:
        category = TextbookCompanionSubCategoryList.objects.using('r')\
            .get(id=subcat_id)
        return category.subcategory
    else:
        category = TextbookCompanionSubCategoryList.objects.using('r')\
            .all().order_by('subcategory')
        return category


def get_subcategories(maincat_id):
    subcategories = TextbookCompanionSubCategoryList.objects.using('r')\
        .filter(maincategory_id=maincat_id).order_by('subcategory_id')
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
    book_id = request.GET.get('book_id')
    user = request.user

    # if not user.is_anonymous():
    #     social = user.social_auth.get(provider='google-oauth2')
    #     url = 'https://www.googleapis.com/plus/v1/people/me'
    #     params = {'access_token': social.extra_data['access_token']}
    #     # r = requests.get(url, params=params)
    #     # print(r.content)

    #     context = {
    #         'user': user
    #     }

    if not (request.GET.get('eid') or request.GET.get('book_id')):
        catg_all = catg(None, all_cat=True)
        subcatg_all = subcatg(None, all_subcat=True)
        context = {
            'catg': catg_all,
            'subcatg': subcatg_all,
        }
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
        template = loader.get_template('index.html')
        return HttpResponse(template.render(context, request))
    elif book_id:
        books = TextbookCompanionPreference.objects\
            .db_manager('r').raw("""
                        SELECT DISTINCT (loc.category_id),pe.id,
                        tcbm.sub_category,loc.maincategory, pe.book as
                        book,loc.category_id,tcbm.sub_category,
                        pe.author as author, pe.publisher as publisher,
                        pe.year as year, pe.id as pe_id, pe.edition,
                        po.approval_date as approval_date
                        FROM textbook_companion_preference pe LEFT JOIN
                        textbook_companion_proposal po ON pe.proposal_id = po.id
                        LEFT JOIN textbook_companion_book_main_subcategories
                        tcbm ON pe.id = tcbm.pref_id LEFT JOIN list_of_category
                        loc ON tcbm.main_category = loc.category_id WHERE
                        po.proposal_status = 3 AND pe.approval_status = 1
                        AND pe.id = tcbm.pref_id AND
                        pe.cloud_pref_err_status = 0 AND
                        pe.id=%s""", [book_id])
        books = list(books)

        if len(books) == 0:
            catg_all = catg(None, all_cat=True)
            context = {
                'catg': catg_all,
                'err_msg': """This book is not supported by Scilab on Cloud."""
                           """ You are redirected to home page."""
            }

            template = loader.get_template('index.html')
            return HttpResponse(template.render(context, request))

        books = get_books(books[0].sub_category)
        maincat_id = books[0].category_id
        subcat_id = books[0].sub_category
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
            'subcategory_id': books[0].sub_category,
            'books': books,
            'book_id': int(book_id),

        }
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
                    cursor.execute(GET_TBC_PREFERENCE_DETAIL_CATEGORY_SQL,
                                   params=[preference_id[0]])
                    books_detail = cursor.fetchone()
                books = get_books(books_detail[1])
                maincat_id = books_detail[0]
                subcat_id = books_detail[1]

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
                template = loader.get_template('index.html')
                return HttpResponse(template.render(context, request))
            subcateg_all = TextbookCompanionSubCategoryList.objects\
                .using('r').filter(maincategory_id=maincat_id)\
                .order_by('subcategory_id')
            categ_all = TextbookCompanionCategoryList.objects.using('r')\
                .filter(~Q(category_id=0)).order_by('maincategory')
            if len(list([ex_views_count[0]])) == 0:
                ex_views_count = 0
            else:
                ex_views_count = ex_views_count[0]
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
