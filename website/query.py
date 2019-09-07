GET_SUBCATEGORY_SQL = """
                SELECT id, subcategory_id, subcategory, maincategory_id
                FROM list_of_subcategory WHERE maincategory_id =%s
                """


GET_TBC_PREFERENCE_SQL = """
                SELECT DISTINCT (loc.category_id), pe.id,
                tcbm.sub_category, loc.maincategory, pe.book as book,
                pe.author as author, pe.publisher as publisher,
                pe.year as year, pe.edition, po.approval_date as approval_date
                FROM textbook_companion_preference pe INNER JOIN
                textbook_companion_proposal po ON pe.proposal_id = po.id
                INNER JOIN textbook_companion_book_main_subcategories tcbm
                ON pe.id = tcbm.pref_id
                INNER JOIN list_of_category loc
                ON tcbm.main_category = loc.category_id
                WHERE po.proposal_status = 3 AND pe.approval_status = 1
                AND pe.id = tcbm.pref_id AND pe.cloud_pref_err_status = 0
                AND loc.category_id = %s AND tcbm.sub_category = %s
                """


GET_TBC_CHAPTER_SQL = """
                SELECT id, number, name FROM textbook_companion_chapter
                WHERE preference_id = %s AND cloud_chapter_err_status = 0
                ORDER BY number
                """


GET_TBC_EXAMPLE_SQL = """
                SELECT id, number, caption FROM textbook_companion_example
                WHERE chapter_id = %s AND cloud_err_status = 0
                ORDER BY number
                """


GET_TBC_EXAMPLE_FILE_SQL = """
                SELECT tcp.id AS id,tcc.id AS chapter_id, tce.id AS example_id,
                tcef.id AS file_id, tcp.directory_name, tcef.filepath
                FROM textbook_companion_preference tcp
                INNER JOIN textbook_companion_chapter tcc
                ON tcp.id = tcc.preference_id
                INNER JOIN textbook_companion_example tce
                ON tcc.id = tce.chapter_id
                INNER JOIN textbook_companion_example_files tcef
                ON tce.id=tcef.example_id
                WHERE tcef.filetype = 'S' AND tcef.example_id = %s
                """


GET_TBC_EXAMPLE_FILE_VIEW_SQL = """
                SELECT id, views_count FROM textbook_companion_example_views
                WHERE example_id = %s
                """


GET_TBC_CONTRIBUTOR_DETAILS_SQL = """
                SELECT preference.id,
                proposal.full_name as proposal_full_name,
                proposal.faculty as proposal_faculty,
                proposal.reviewer as proposal_reviewer,
                proposal.university as proposal_university
                FROM textbook_companion_proposal proposal
                INNER JOIN textbook_companion_preference preference
                ON proposal.id = preference.proposal_id
                WHERE preference.id = %s
