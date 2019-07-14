from collections import Counter
import sys
import json
from multiprocessing import Process
from time import sleep
import os
import logging
from flask import Flask, g, request, jsonify, send_from_directory, abort
from models import get_database, create_tables
from models import Bite, Apple
from models import STATUS_PROCESSING, STATUS_COMPLETE, STATUS_STOPPED
logging.basicConfig(level=logging.INFO)
LOG_LVL = logging.INFO
logger = logging.getLogger(__name__)

app = Flask(__name__)
UPLOAD_DIR = 'local_uploads'

AGGREGATION_TECHNIQUES = [
    "majority",  # the majority
    "found-majority",  # the majority ignoring the slice with no subject column
]

@app.route('/')
def hello_world():
    return 'Hello World! This is Election'


@app.route('/add', methods=["GET", "POST"])
def add_bite():
    table_name = request.values.get('table').strip()
    column = int(request.values.get('subject_col_id'))
    # if 'subject_col_id' in request.values:
    #     column = int(request.values.get('subject_col_id'))
    # else:
    #     column = int(request.values.get('col_id'))
    slice = int(request.values.get('slice'))
    tot = int(request.values.get('total'))  # total number of slices

    agg_technique = request.values.get('technique')  # aggregation technique
    if agg_technique not in AGGREGATION_TECHNIQUES:
        return jsonify(error="Invalid aggregation technique"), 400

    apples = Apple.select().where(Apple.table==table_name)
    if len(apples) == 0:
        logger.log(LOG_LVL, "\nNew apple: table=%s, columns=%d, slice=%d ,total=%d" % (table_name, column, slice, tot))
        apple = Apple(table=table_name, total=tot)
        apple.save()
    else:
        apple = apples[0]
        logger.log(LOG_LVL, "\nExisting apple: table=%s, columns=%d, slice=%d ,total=%d" % (table_name, column, slice, tot))

    if apple.complete:
        return jsonify(error="The apple is already complete, your request will not be processed"), 400

    b = Bite(apple=apple, slice=slice, col_id=column)
    b.save()

    slices = []
    for bite in apple.bites:
        slices.append(bite.slice)
    if sorted(slices) == range(apple.total):
        apple.complete = True
        apple.save()

    if apple.complete:
        # if app.testing:
        #     combine_graphs(apple.id)
        # else:
        #     g.db.close()
        #     p = Process(target=combine_graphs, args=(apple.id,))
        #     p.start()
        g.db.close()
        p = Process(target=elect, args=(apple.id, agg_technique))
        p.start()
    return jsonify({"apple": apple.id, "bite": b.id})


@app.route('/status', methods=["GET"])
def status():
    # apples = [{"apple": apple.table, "status": apple.status, "complete": apple.complete} for apple in Apple.select()]
    apples = [{"apple": apple.table, "status": apple.status, "complete": apple.complete, "elected": apple.elected, "agreement": apple.agreement} for apple in Apple.select()]
    return jsonify(apples=apples)


@app.route('/list', methods=["GET"])
def all_apples():
    return jsonify(apples=[apple.json() for apple in Apple.select()])


@app.route('/list_bites', methods=["GET"])
def all_bites():
    return jsonify(bites=[b.json() for b in Bite.select()])


@app.before_request
def before_request():
    g.db = get_database()
    g.db.connect(reuse_if_open=True)


@app.after_request
def after_request(response):
    g.db.close()
    return response


def elect(apple_id, technique):
    """
    :param apple_id:
    :return: most_frequent, agreement (how many agreed on this).
    """
    database = get_database()
    database.connect(reuse_if_open=True)
    apples = Apple.select().where(Apple.id==apple_id)
    if len(apples) == 0:
        logger.error("Apple with id: %s does not exists" % str(apple_id))
        database.close()
        return
        # return None, None
    apple = apples[0]
    apple.status = STATUS_PROCESSING
    apple.save()
    try:
        col_ids = [b.col_id for b in apple.bites]
        # c = Counter(col_ids)
        # sorted_cols_counts = sorted(c.items(), key=lambda item: item[1])
        # most_frequent_col_id = sorted_cols_counts[-1][0]
        # agreement = sorted_cols_counts[-1][1]*1.0/len(col_ids)
        if technique =="majority":
            elected_col_id, agreement = majority_aggregation(col_ids)
        elif technique == "found-majority":
            elected_col_id, agreement = found_majority_aggregation(col_ids)
        else:
            logger.error("unvalid technique: <%s>" % technique)
            apple.status = STATUS_STOPPED
            apple.save()
            return
        apple.elected = elected_col_id
        apple.agreement = agreement
        apple.status = STATUS_COMPLETE
        apple.save()
    except Exception as e:
        logger.error(str(e))
        apple.status = STATUS_STOPPED
        apple.save()
    database.close()
    # return most_frequent_col_id, agreement


def majority_aggregation(col_ids):
    """
    :param col_ids:
    :return:
    """
    c = Counter(col_ids)
    sorted_cols_counts = sorted(c.items(), key=lambda item: (item[1], item[0]))
    most_frequent_col_id = sorted_cols_counts[-1][0]
    agreement = sorted_cols_counts[-1][1] * 1.0 / len(col_ids)
    return most_frequent_col_id, agreement


def found_majority_aggregation(col_ids):
    """
    :param col_ids:
    :return:
    """
    c = Counter(col_ids)
    if len(c.keys()) > 1:
        del c[-1]
    # sort by the frequency, and if two has the same frequency favor the left most
    sorted_cols_counts = sorted(c.items(), key=lambda item: (item[1], item[0]))
    most_frequent_col_id = sorted_cols_counts[-1][0]
    agreement = sorted_cols_counts[-1][1] * 1.0 / len(col_ids)
    return most_frequent_col_id, agreement


if __name__ == '__main__':
    create_tables()
    if 'port' in os.environ:
        app.run(debug=True, host='0.0.0.0', port=int(os.environ['port']))
    else:
        app.run(debug=True, host='0.0.0.0')

