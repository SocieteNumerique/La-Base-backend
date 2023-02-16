from django.shortcuts import render
from django.views import View

from django.core.files.storage import FileSystemStorage

from main.management.commands.import_cnfs_accounts import import_accounts
from moine_back.settings import BASE_DIR


class UpdateCnfsAccountsView(View):
    get_template_name = "admin/upload_cnfs_file.html"
    post_template_name = "admin/upload_cnfs_file_done.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.get_template_name, {})

    def post(self, request, *args, **kwargs):
        file = request.FILES["file"]
        fs = FileSystemStorage(location=BASE_DIR)
        fs.save("cnfs_accounts.csv", file)
        account_emails = import_accounts(max_n_accounts=1)
        return render(request, self.post_template_name, {"created": account_emails})
