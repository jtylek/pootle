# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from .utils import RelatedStoresDataTool


class DirectoryDataTool(RelatedStoresDataTool):
    """Retrieves aggregate stats for a Directory"""

    group_by = ("store__parent__pootle_path", )

    def filter_data(self, qs):
        return qs.filter(
            store__parent__pootle_path__startswith=self.context.pootle_path)

    @property
    def children_stats(self):
        children = {}
        for child in self.child_stats_qs.iterator():
            self.add_child_stats(children, child)
        child_stores = self.data_model.filter(store__parent=self.context).values(
            *("store__name", ) + self.max_fields + self.sum_fields)
        for child in child_stores:
            self.add_child_stats(
                children,
                child,
                root=child["store__name"],
                use_aggregates=False)
        self.add_submission_info(self.stat_data, children)
        self.add_last_updated_info(child_stores, children)
        return children

    @property
    def child_stats_qs(self):
        return super(
            DirectoryDataTool,
            self).child_stats_qs.exclude(store__parent=self.context)

    def get_root_child_path(self, child):
        return (
            child["store__parent__pootle_path"].replace(
                self.context.pootle_path, "").split("/")[0])
