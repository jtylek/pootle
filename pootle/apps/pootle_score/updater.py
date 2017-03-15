# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import date

from django.utils.functional import cached_property

from pootle.core.delegate import log, event_score
from pootle_log.utils import LogEvent
from pootle_score.models import UserStoreScore


class StoreScoreUpdater(object):
    event_class = LogEvent
    score_model = UserStoreScore

    def __init__(self, store, *args, **kwargs):
        self.store = store
        self.user = kwargs.get('user')

    @cached_property
    def logs(self):
        return log.get(self.store.__class__)(self.store)

    @cached_property
    def scoring(self):
        return event_score.gather(self.event_class)

    def score_event(self, event, calculated_scores):
        if event.action not in self.scoring:
            return
        scores = self.scoring[event.action](event).get_score()
        if not scores or not any(x > 0 for x in scores.values()):
            return
        calculated_scores[event.timestamp] = (
            calculated_scores.get(event.timestamp, {}))
        calculated_scores[event.timestamp][event.user.id] = (
            calculated_scores[event.timestamp].get(event.user.id, {}))
        for k, score in scores.items():
            if not score:
                continue
            calculated_scores[event.timestamp][event.user.id][k] = (
                calculated_scores[event.timestamp][event.user.id].get(k, 0)
                + score)

    def calculate(self, start=date.today(), end=None):
        calculated_scores = {}
        scored_events = self.logs.get_events(
            user=self.user, start=start, end=end)
        for event in scored_events:
            self.score_event(event, calculated_scores)
        return calculated_scores

    def iterate_scores(self, scores):
        for timestamp, date_scores in scores.items():
            for user, user_scores in date_scores.items():
                yield timestamp, user, user_scores

    def find_existing_scores(self, scores):
        existing_scores = self.score_model.objects.none()
        score_iterator = self.iterate_scores(scores)
        for timestamp, user, user_scores in score_iterator:
            existing_scores = (
                existing_scores
                | self.score_model.objects.filter(
                    user_id=user,
                    store_id=self.store.id,
                    date=timestamp))
        return existing_scores

    def delete_scores(self, scores):
        self.find_existing_scores(
            scores).select_for_update().delete()

    def new_scores(self, scores):
        score_iterator = self.iterate_scores(scores)
        for timestamp, user, user_scores in score_iterator:
            yield self.score_model(
                date=timestamp,
                user_id=user,
                store_id=self.store.id,
                **user_scores)

    def create_scores(self, scores):
        self.score_model.objects.bulk_create(self.new_scores(scores))

    def set_scores(self, calculated_scores):
        self.delete_scores(calculated_scores)
        self.create_scores(calculated_scores)

    def update(self):
        self.set_scores(self.calculate())
