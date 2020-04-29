# -*- coding:utf-8 -*-
# Created by LuoJie at 4/29/19
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def evaluate_score(y_true, y_pred):
    print('accuracy_score', accuracy_score(y_true, y_pred))
    print('para_recall', recall_score(y_true, y_pred, average=None))
    print('para_precision', precision_score(y_true, y_pred, average=None))
    print('macro-precision:', precision_score(y_true, y_pred, average='macro'))
    print('micro-precision:', precision_score(y_true, y_pred, average='micro'))
    print('macro-recall:', recall_score(y_true, y_pred, average='macro'))
    print('micro-recall:', recall_score(y_true, y_pred, average='micro'))
    print('macro-f1:', f1_score(y_true, y_pred, average='macro'))
    print('micro-f1:', f1_score(y_true, y_pred, average='micro'))
