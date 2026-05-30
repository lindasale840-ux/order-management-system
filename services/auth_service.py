from repositories.user_repository import (
    UserRepository
)

from utils.password_utils import (
    verify_password
)


class AuthService:

    @staticmethod
    def login(

        username,

        password

    ):

        user = (
            UserRepository
            .get_user_by_username(
                username
            )
        )

        if not user:

            return None

        valid_password = (

            verify_password(

                password,

                user[
                    "password_hash"
                ]
            )
        )

        if not valid_password:

            return None

        return {

            "username":
            user["username"],

            "role":
            user["role"]
        }