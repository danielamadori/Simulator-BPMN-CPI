def _id_gen():
    i = 0
    while True:
        yield str(i)
        i += 1


gen = _id_gen()


def new_id():
    return next(gen)


_task_counter = 0
_parallel_counter = 0
_choice_counter = 0
_nature_counter = 0
_loop_counter = 0


def _next_task_label():
    global _task_counter
    _task_counter += 1
    return f"T{_task_counter}"


def _next_parallel_label():
    global _parallel_counter
    _parallel_counter += 1
    return f"P{_parallel_counter}"


def _next_choice_label():
    global _choice_counter
    _choice_counter += 1
    return f"C{_choice_counter}"


def _next_nature_label():
    global _nature_counter
    _nature_counter += 1
    return f"N{_nature_counter}"


def _next_loop_label():
    global _loop_counter
    _loop_counter += 1
    return f"L{_loop_counter}"


def task(label=None, duration=1.0, impacts=None):
    if impacts is None:
        impacts = [1.0]
    if label is None:
        label = _next_task_label()
    return {
        "id": new_id(),
        "type": "task",
        "label": label,
        "duration": duration,
        "impacts": impacts,
    }


def sequential(children):
    if not children:
        return {
            "id": new_id(),
            "type": "sequential",
            "children": [],
        }
    if len(children) <= 2:
        return {
            "id": new_id(),
            "type": "sequential",
            "children": children,
        }
    current = children[0]
    for child in children[1:]:
        current = {
            "id": new_id(),
            "type": "sequential",
            "children": [current, child],
        }
    return current


def parallel(children, label=None):
    if label is None:
        label = _next_parallel_label()
    return {
        "id": new_id(),
        "type": "parallel",
        "label": label,
        "children": children,
    }


def choice(children, max_delay=0.0, label=None):
    if label is None:
        label = _next_choice_label()
    return {
        "id": new_id(),
        "type": "choice",
        "label": label,
        "children": children,
        "max_delay": max_delay,
    }


def nature(children, distribution, label=None):
    if label is None:
        label = _next_nature_label()
    return {
        "id": new_id(),
        "type": "nature",
        "label": label,
        "children": children,
        "distribution": distribution,
    }


def loop(child, label=None, probability=0.5, bound=5):
    if label is None:
        label = _next_loop_label()
    return {
        "id": new_id(),
        "type": "loop",
        "label": label,
        "children": [child],
        "distribution": probability,
        "bound": bound,
    }


def get_patterns():
    patterns = []

    patterns.append({
        "name": "Single Task",
        "expr": "R1",
        "json": task(),
    })

    patterns.append({
        "name": "Sequence Two",
        "expr": "R1, R2",
        "json": sequential([task(), task()]),
    })

    patterns.append({
        "name": "Choice",
        "expr": "R1 /[C1] R2",
        "json": choice([task(), task()]),
    })

    patterns.append({
        "name": "Parallel",
        "expr": "R1 || R2",
        "json": parallel([task(), task()]),
    })

    patterns.append({
        "name": "Loop",
        "expr": "<R1 [L1]>",
        "json": loop(task(), probability=0.7),
    })

    patterns.append({
        "name": "Nature",
        "expr": "^[N1] (R1, R2)",
        "json": nature([task(), task()], distribution=[0.3, 0.7]),
    })

    patterns.append({
        "name": "Sequential + Parallel",
        "expr": "R1, (R2 || R3), R4",
        "json": sequential([
            task(),
            sequential([
                parallel([task(), task()]),
                task(),
            ]),
        ]),
    })

    patterns.append({
        "name": "Sequential + Choice",
        "expr": "R1, (R2 /[C1] R3), R4",
        "json": sequential([
            task(),
            sequential([
                choice([task(), task()]),
                task(),
            ]),
        ]),
    })

    patterns.append({
        "name": "Sequential + Loop",
        "expr": "R1, <R2 [L1]>, R3",
        "json": sequential([
            task(),
            sequential([
                loop(task()),
                task(),
            ]),
        ]),
    })

    patterns.append({
        "name": "Sequential + Nature",
        "expr": "R1, ^[N1] (R2, R3), R4",
        "json": sequential([
            task(),
            sequential([
                nature([task(), task()], distribution=[0.4, 0.6]),
                task(),
            ]),
        ]),
    })

    patterns.append({
        "name": "Complex Parallel",
        "expr": "R1, ((R2 /[C1] R3) || <R4 [L1]>), R5",
        "json": sequential([
            task(),
            sequential([
                parallel([
                    choice([task(), task()]),
                    loop(task()),
                ]),
                task(),
            ]),
        ]),
    })

    patterns.append({
        "name": "Parallel Choice Simple",
        "expr": "((R2 /[C1] R3) || R4)",
        "json": parallel([
            choice([task(), task()]),
            task(),
        ]),
    })

    patterns.append({
        "name": "Choice of Parallels",
        "expr": "(R1 || R2) /[C1] (R3 || R4)",
        "json": choice([
            parallel([task(), task()]),
            parallel([task(), task()]),
        ]),
    })

    patterns.append({
        "name": "Parallel with Loop",
        "expr": "R1 || <R2 [L1]>",
        "json": parallel([
            task(),
            loop(task()),
        ]),
    })

    patterns.append({
        "name": "Sequential in Parallel",
        "expr": "(R1, R2) || (R3, R4)",
        "json": parallel([
            sequential([task(), task()]),
            sequential([task(), task()]),
        ]),
    })

    patterns.append({
        "name": "Nested Choice",
        "expr": "(R1 /[C1] R2) /[C2] R3",
        "json": choice([
            choice([task(), task()]),
            task(),
        ]),
    })

    patterns.append({
        "name": "Loop containing Parallel",
        "expr": "<(R1 || R2) [L1]>",
        "json": loop(parallel([task(), task()])),
    })

    patterns.append({
        "name": "Loop containing Choice",
        "expr": "<(R1 /[C1] R2) [L1]>",
        "json": loop(choice([task(), task()])),
    })

    patterns.append({
        "name": "Loop containing Nature",
        "expr": "<^[N1] (R1, R2) [L1]>",
        "json": loop(nature([task(), task()], distribution=[0.5, 0.5])),
    })

    patterns.append({
        "name": "Nested Loops",
        "expr": "<<R1 [L1]> [L2]>",
        "json": loop(loop(task())),
    })

    patterns.append({
        "name": "Nature containing Parallel",
        "expr": "^[N1] ((R1 || R2), R3)",
        "json": nature([parallel([task(), task()]), task()], distribution=[0.6, 0.4]),
    })

    patterns.append({
        "name": "Nature containing Choice",
        "expr": "^[N1] ((R1 /[C1] R2), R3)",
        "json": nature([choice([task(), task()]), task()], distribution=[0.5, 0.5]),
    })

    patterns.append({
        "name": "Nature containing Loop",
        "expr": "^[N1] (<R1 [L1]>, R2)",
        "json": nature([loop(task()), task()], distribution=[0.7, 0.3]),
    })

    patterns.append({
        "name": "Choice containing Nature",
        "expr": "^[N1](R1, R2) /[C1] R3",
        "json": choice([nature([task(), task()], distribution=[0.5, 0.5]), task()]),
    })

    patterns.append({
        "name": "Choice containing Loop",
        "expr": "<R1 [L1]> /[C1] R2",
        "json": choice([loop(task()), task()]),
    })

    patterns.append({
        "name": "Parallel Three Branches",
        "expr": "R1 || R2 || R3",
        "json": parallel([task(), task(), task()]),
    })

    patterns.append({
        "name": "Parallel in Loop in Sequence",
        "expr": "R1, <(R2 || R3) [L1]>, R4",
        "json": sequential([
            task(),
            sequential([
                loop(parallel([task(), task()])),
                task(),
            ]),
        ]),
    })

    patterns.append({
        "name": "Parallel containing Nature",
        "expr": "R1 || ^[N1](R2, R3)",
        "json": parallel([
            task(),
            nature([task(), task()], distribution=[0.5, 0.5]),
        ]),
    })

    patterns.append({
        "name": "Nested Parallel",
        "expr": "(R1 || R2) || R3",
        "json": parallel([
            parallel([task(), task()]),
            task(),
        ]),
    })

    patterns.append({
        "name": "Choice containing Sequential",
        "expr": "(R1, R2) /[C1] R3",
        "json": choice([
            sequential([task(), task()]),
            task(),
        ]),
    })

    patterns.append({
        "name": "Nature containing Sequential",
        "expr": "^[N1]((R1, R2), R3)",
        "json": nature([
            sequential([task(), task()]),
            task(),
        ], distribution=[0.6, 0.4]),
    })

    patterns.append({
        "name": "Loop containing Sequential",
        "expr": "<(R1, R2) [L1]>",
        "json": loop(sequential([task(), task()])),
    })

    patterns.append({
        "name": "Nested Nature",
        "expr": "^[N1](^[N2](R1, R2), R3)",
        "json": nature([
            nature([task(), task()], distribution=[0.5, 0.5]),
            task(),
        ], distribution=[0.7, 0.3]),
    })

    patterns.append({
        "name": "Massive Parallel",
        "expr": "Massive Parallel (8 branches)",
        "json": parallel([task() for _ in range(8)]),
    })

    patterns.append({
        "name": "Deep Sequence",
        "expr": "T1 -> T2 -> ... -> T10",
        "json": sequential([task() for _ in range(10)]),
    })

    patterns.append({
        "name": "Wide Parallel",
        "expr": "(T1->...->T5) || T6",
        "json": parallel([
            sequential([task() for _ in range(5)]),
            task(),
        ]),
    })

    patterns.append({
        "name": "Kitchen Sink",
        "expr": "< ^[N]( [C]( (T||T), T ), T ) [L] >",
        "json": loop(
            nature([
                choice([
                    parallel([task(), task()]),
                    task(),
                ]),
                task(),
            ], distribution=[0.8, 0.2])
        ),
    })

    patterns.append({
        "name": "Deep Loop Nesting",
        "expr": "L3(L2(L1(T)))",
        "json": loop(loop(loop(task()))),
    })

    return patterns
