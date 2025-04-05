import collections
import itertools
import linecache
import sys
import traceback


class StackSummaryWrapper(traceback.StackSummary):
    @classmethod
    def extract(klass, frame_gen, *, limit=None, lookup_lines=True, capture_locals=True):
        def extended_frame_gen():
            for f, lineno in frame_gen:
                yield f, lineno

        return klass._extract_from_extended_frame_gen(
            extended_frame_gen(),
            limit=limit,
            lookup_lines=lookup_lines,
            capture_locals=capture_locals,
        )

    @classmethod
    def _extract_from_extended_frame_gen(
        klass, frame_gen, *, limit=None, lookup_lines=True, capture_locals=False
    ):
        if limit is None:
            limit = getattr(sys, "tracebacklimit", None)
            if limit is not None and limit < 0:
                limit = 0
        if limit is not None:
            if limit >= 0:
                frame_gen = itertools.islice(frame_gen, limit)
            else:
                frame_gen = collections.deque(frame_gen, maxlen=-limit)

        result = klass()
        fnames = set()
        for f, lineno in frame_gen:
            co = f.f_code
            filename = co.co_filename
            name = co.co_name

            fnames.add(filename)
            linecache.lazycache(filename, f.f_globals)

            f_locals = f.f_locals if capture_locals else None

            try:
                frame_summary = traceback.FrameSummary(
                    filename,
                    lineno,
                    name,
                    lookup_line=False,
                    locals=f_locals,
                )
            except Exception:
                continue
            result.append(frame_summary)
        for filename in fnames:
            linecache.checkcache(filename)
        return result
