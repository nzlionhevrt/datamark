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

def get_data():

    import numpy as np
    import imageio
    import pickle
    import os

    data = {}

    imgs_path = os.path.join(request.folder, 'static','checked_images')

    for mark in range(3):

        d = db(db.dataset.mark == mark).select()

        imgs = []

        for img in d:
            if os.path.isfile(os.path.join(imgs_path, img.name)):
                image = imageio.imread(os.path.join(imgs_path, img.name))
                imgs.append(image)

        data[str(mark)] = imgs

    pickle_rick_path = os.path.join(request.folder,
                                    'uploads',
                                    'data',
                                    'rick.pickle')

    with open(pickle_rick_path, 'wb') as f:
        pickle.dump(data, f)

    redirect(URL('pickle_rick'))

    return dict()

def pickle_rick():
    import os
    pickle_rick_path = os.path.join(request.folder,
                                    'uploads',
                                    'data',
                                    'rick.pickle')
    response.stream(pickle_rick_path, attachment=True, filename='rick.pickle')

def null():
    state = "All work is done. Relax."
    return dict(state=state)

@cache.action()
def download():
    return response.download(request, db)
