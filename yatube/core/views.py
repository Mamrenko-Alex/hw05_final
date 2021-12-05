from django.shortcuts import render


def page_not_found(request, exception):
    template = 'core/404.html'
    context = {'path':request.path}
    status = 404
    return render(request, template, context, status=status)

def csrf_failure(request, reason=''):
    template = 'core/403.html'
    status = 403
    return render(request, template, status=status)

def server_error(request):
    template = 'core/500.html'
    status = 500
    return render(request, template, status=status)
