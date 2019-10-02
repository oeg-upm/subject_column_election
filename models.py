from peewee import SqliteDatabase, Model, CharField, IntegerField, ForeignKeyField, BooleanField, FloatField

DATABASE = 'data.db'

local_database = SqliteDatabase(DATABASE)


def get_database(database=None):
    if database is None:
        database = DATABASE

    return local_database


class BaseModel(Model):
    class Meta:
        database = get_database()


STATUS_NEW, STATUS_PROCESSING, STATUS_COMPLETE, STATUS_STOPPED = "New", "Processing", "Complete", "Stopped"
APPLE_STATUSES = [
    STATUS_NEW, STATUS_PROCESSING, STATUS_COMPLETE, STATUS_STOPPED
]


class Apple(BaseModel):
    table = CharField(unique=True)  # table name or id
    status = CharField(default=STATUS_NEW, choices=APPLE_STATUSES)  # the status of merging
    complete = BooleanField(default=False)  # Whether there are missing slices or not
    total = IntegerField()  # the total number of slices
    elected = IntegerField(null=True)  # the elected subject column
    agreement = FloatField(null=True)  # the percentage of bites agreeing on the elected subject column

    def json(self):
        return {
            "id": self.id,
            "table": self.table,
            "status": self.status,
            "complete": self.complete,
        }


class Bite(BaseModel):
    slice = IntegerField()  # slice order (position)
    apple = ForeignKeyField(Apple, backref='bites')
    col_id = IntegerField()  # the id of the suggested subject column

    def json(self):
        return {
            "id": self.id,
            "slice": self.slice,
            "apple": self.apple.json(),
            "col_id": self.col_id,
        }


def create_tables():
    print("creating tables ...\n\n")
    database = get_database()
    with database:
        database.create_tables([Apple, Bite, ], safe=True)



