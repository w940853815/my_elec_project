"""flask restfule common."""
from flask import Blueprint
from flask_restful import Api, Resource, abort

api_bp = Blueprint('api_bp', __name__, url_prefix='/v1/api/')
api_rest = Api(api_bp)


class BaseResource(Resource):
    """override Resource."""

    def get(self, *args, **kwargs):
        """Get method."""
        abort(405)

    def post(self, *args, **kwargs):
        """Post method."""
        abort(405)

    def put(self, *args, **kwargs):
        """Put method."""
        abort(405)

    def patch(self, *args, **kwargs):
        """Patch method."""
        abort(405)

    def delete(self, *args, **kwargs):
        """Delete method."""
        abort(405)


def rest_resource(resource_cls):
    """Decorate for adding resources to Api App."""
    api_rest.add_resource(resource_cls, *resource_cls.endpoints)
