from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.views import View


class TestErrors(View):

    def get(self, request):

        user = request.user

        if user.is_superuser:

            html = """
                    <!DOCTYPE html>
                    <html lang="en">
                      <body>
                        <ul>
                            <li><a href="/">home</a></li>
                            <li><a href="?action=raise403">Raise Error 403</a></li>
                            <li><a href="?action=raise404">Raise Error 404</a></li>
                            <li><a href="?action=raise500">Raise Error 500</a></li>
                        </ul>
                        <form method="post">
                            <input type="submit">
                        </form>
                      </body>
                    </html>
                    """

            action = request.GET.get('action', '')
            if action == 'raise403':
                raise PermissionDenied
            elif action == 'raise404':
                raise Http404
            elif action == 'raise500':
                raise Exception('Server error')

            return HttpResponse(html)

        else:
            raise Http404
