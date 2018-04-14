# -*- coding: utf-8 -*-

@auth.requires_login()
def api_get_user_email():
    if not request.env.request_method == 'GET': raise HTTP(403)
    return response.json({'status':'success', 'email':auth.user.email})

@auth.requires_membership('admin') # can only be accessed by members of admin groupd
def grid():
    response.view = 'generic.html' # use a generic view
    tablename = request.args(0)
    if not tablename in db.tables: raise HTTP(403)
    grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
    return dict(grid=grid)

def wiki():
    auth.wikimenu()
    return auth.wiki()

def user():
    return dict(form=auth())

def stats():

    images = db(db.image_list).count()
    first_class = db(db.dataset.mark == 0).count()
    second_class = db(db.dataset.mark == 1).count()
    skipped = db(db.dataset.mark == 2).count()

    return dict(images = images, first_class = first_class, second_class = second_class, skipped = skipped)

@auth.requires_membership('admin')
def refresh():

    import os

    Files = os.listdir('applications/datamark/static/unchecked_images/')

    for name in Files:
        if db(db.image_list.name == name).count() == 0: db.image_list.insert(name=name)

    state = "Succseed!"

    return dict(state=state)

def mark():

    import os

    if db(db.image_list).select(limitby=(0,1)):

        img_name = db().select(db.image_list.ALL, orderby='<random>', limitby=(0,1))[0].name
        class1_button = FORM(INPUT(_type='submit', _value='Первый класс'), _action=URL('submit_mark', vars=dict(img_name=img_name, mark=0)))
        class2_button = FORM(INPUT(_type='submit', _value='Второй класс'), _action=URL('submit_mark', vars=dict(img_name=img_name, mark=1)))
        skip_button = FORM(INPUT(_type='submit', _value='Пропустить'), _action=URL('submit_mark', vars=dict(img_name=img_name, mark=2)))

        return dict(img_name = img_name, class1_button = class1_button, class2_button = class2_button, skip_button = skip_button)

    else:
        redirect(URL('null'))

def check():
    images = db().select(db.image_list.ALL)
    return dict(images=images)

def submit_mark():

    import os

    db.dataset.insert(name=request.vars.img_name, mark=request.vars.mark)

    try:
        os.rename(os.path.join(request.folder, 'static','unchecked_images', request.vars.img_name),
                  os.path.join(request.folder, 'static','checked_images', request.vars.img_name))

    except FileNotFoundError:
        db(db.image_list.name == request.vars.img_name).delete()
        redirect(URL('mark'))

    db(db.image_list.name == request.vars.img_name).delete()
    redirect(URL('mark'))
    return dict()

def make_archive():

    import tarfile
    import os

    def make_tarfile(output_filename, source_dir):
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

    imgs_path = os.path.join(request.folder, 'static','checked_images')


    tar_file_path = os.path.join(request.folder, 'uploads', 'data', 'rox.tar.gz')

    if not os.path.exists(tar_file_path):
        os.makedirs(directory)

    make_tarfile(tar_file_path, imgs_path)

    return dict()

def get_archive():

    import os

    tar_file_path = os.path.join(request.folder, 'uploads', 'data', 'rox.tar.gz')

    response.stream(tar_file_path, attachment=True, filename='rox.tar.gz')

def get_labels_info():

    import os

    data = {"0": [row.name for row in db(db.dataset.mark==0).select()],
            "1": [row.name for row in db(db.dataset.mark==1).select()],
            "2": [row.name for row in db(db.dataset.mark==2).select()]}

    labels_file_path = os.path.join(request.folder, 'uploads', 'data', 'labels.txt')

    with open(labels_file_path, 'w') as File:
        File.write(str(data))

    response.stream(labels_file_path, attachment=True, filename='labels.txt')

    return dict()

def null():
    state = "All work is done. Relax."
    return dict(state=state)

@cache.action()
def download():
    return response.download(request, db)
