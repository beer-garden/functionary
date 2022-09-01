from django.db import transaction


class ModelSaveHookMixin:
    """This mixin provides access to hooks for actions to take place before or after
    save and creation. To use it, simply include this mixin and then override any of
    the following methods:

        pre_create
        pre_save
        post_create
        post_save

    These methods are run, in that order, inside of a transaction during the model's
    save() call. The pre_create and post_create are only run on newly created instances
    and not any subsequent updates.  If an exception is raised at any point in any of
    the methods or the save() itself, all database activity will be rolled back.
    """

    def pre_create(self):
        """Actions to run before create"""
        pass

    def post_create(self):
        """Actions to run after create"""
        pass

    def pre_save(self):
        """Actions to run before save"""
        pass

    def post_save(self):
        """Actions to run after save"""
        pass

    def save(self, *args, **kwargs):
        """Custom save that calls the pre and post save hooks inside of a
        transaction"""
        creating = self._state.adding

        with transaction.atomic():
            if creating:
                self.pre_create()

            self.pre_save()

            super().save(*args, **kwargs)

            if creating:
                self.post_create()

            self.post_save()

        return self
