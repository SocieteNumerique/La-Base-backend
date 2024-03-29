from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from main.query_changes.utils import query_my_related_tags


class UserManager(BaseUserManager):
    def create_user(
        self,
        email: str,
        first_name="",
        last_name="",
        password=None,
        is_active=False,
        is_admin=False,
        is_superuser=False,
        cnfs_id=None,
        cnfs_id_organization=None,
    ):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_admin=is_admin,
            is_superuser=is_superuser,
            cnfs_id=cnfs_id,
            cnfs_id_organization=cnfs_id_organization,
        )
        if password.startswith("pbkdf2_sha256"):
            user.password = password
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        first_name="",
        last_name="",
        password=None,
        is_active: bool = True,
    ):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_active = is_active
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    username = None
    email = models.EmailField(
        verbose_name="adresse email",
        max_length=255,
        unique=True,
    )
    first_name = models.CharField(verbose_name="prénom", max_length=100, default="")
    last_name = models.CharField(verbose_name="nom", max_length=100, default="")
    is_active = models.BooleanField(verbose_name="email validé", default=True)
    is_admin = models.BooleanField(verbose_name="est admin", default=False)
    is_superuser = models.BooleanField(
        verbose_name="est super-utilisateur", default=False
    )

    tags = models.ManyToManyField(
        "Tag",
        blank=True,
        related_name="users",
        limit_choices_to=query_my_related_tags("User"),
    )

    cnfs_id = models.PositiveIntegerField(verbose_name="id CNFS", null=True, blank=True)
    cnfs_id_organization = models.PositiveIntegerField(
        verbose_name="est employeur de l'id CNFS", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        names = []
        if self.first_name:
            names.append(self.first_name)
        if self.last_name:
            names.append(self.last_name)
        if not len(names):
            return self.email
        return " ".join(names)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
