from django.http import JsonResponse
from django.views import View

from .services import RoutePlannerError, build_plan


class RouteFuelPlanView(View):
    http_method_names = ['get', 'options']

    def get(self, request):
        start = request.GET.get('start') or request.GET.get('start_location')
        finish = request.GET.get('finish') or request.GET.get('finish_location')
        if not start or not finish:
            return JsonResponse({'error': 'Both start and finish query parameters are required.'}, status=400)
        try:
            print(f"Received route fuel plan request: start='{start}', finish='{finish}'")
            return JsonResponse(build_plan(start, finish))
        except RoutePlannerError as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        except Exception as exc:
            return JsonResponse({'error': 'Unable to build route fuel plan.', 'detail': str(exc)}, status=502)
