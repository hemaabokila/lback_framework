class DebugMiddleware:
    def __init__(self, enabled=True, log_request=True, log_response=True, max_body_length=500):
        self.enabled = enabled
        self.log_request = log_request
        self.log_response = log_response
        self.max_body_length = max_body_length

    def process_request(self, request):
        if self.enabled and self.log_request:
            print(f"Request: {request.path}, Method: {request.method}")
            
            headers = request.headers if request.headers else "No Headers"
            print(f"Headers: {headers}")
            
            if request.body:
                body = request.body[:self.max_body_length] 
                print(f"Body: {body if len(request.body) <= self.max_body_length else body + '...'}")
            else:
                print("No Body")

    def process_response(self, request, response):
        if self.enabled and self.log_response:
            print(f"Response Status Code: {response['status_code']}")
            
            if 'body' in response:
                body = response['body'][:self.max_body_length]
                print(f"Response Body: {body if len(response['body']) <= self.max_body_length else body + '...'}")
            else:
                print("No Response Body")
        
        return response
