import time


class StatsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        start_time = time.time()        
        response = self.get_response(request)
        duration = time.time() - start_time

        response["X-Page-Generation_duration-ms"] = int(duration * 1000)
        return response
