import logging

class ErrorHandler:
    def __init__(self):
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def handle_404(self, request):
        self.logger.warning(f"404 Error: Path '{request.path}' not found.")
        return {"status_code": 404, "body": "Not Found"}

    def handle_500(self, error):
        self.logger.error("500 Error: Internal Server Error", exc_info=error)
        return {"status_code": 500, "body": "Internal Server Error"}

    def handle_custom_error(self, status_code, message):
        if status_code == 404:
            self.logger.warning(f"Custom 404 Error: {message}")
        elif status_code == 500:
            self.logger.error(f"Custom 500 Error: {message}")
        else:
            self.logger.error(f"Error {status_code}: {message}")
        
        return {"status_code": status_code, "body": message}

    def handle_exception(self, exception):
        self.logger.error("Unhandled Exception: ", exc_info=exception)
        return self.handle_500(exception)

