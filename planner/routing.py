from .providers import DemoProvider, OSRMProvider


def cost(order, matrix, return_to_start):
    path = [0] + order + ([0] if return_to_start else [])
    return sum(matrix[a][b] for a, b in zip(path, path[1:]))


def optimize_order(matrix, return_to_start):
    remaining = set(range(1, len(matrix)))
    order = []
    current = 0
    while remaining:
        current = min(remaining, key=lambda n: (matrix[current][n], n))
        order.append(current)
        remaining.remove(current)
    # Full directed cost is essential: road matrices need not be symmetric.
    for _ in range(100):
        baseline = cost(order, matrix, return_to_start)
        best, best_cost = order, baseline
        for i in range(len(order) - 1):
            for j in range(i + 1, len(order)):
                candidate = order[:i] + order[i:j+1][::-1] + order[j+1:]
                candidate_cost = cost(candidate, matrix, return_to_start)
                if candidate_cost < best_cost - 1e-7:
                    best, best_cost = candidate, candidate_cost
        if best_cost >= baseline - 1e-7:
            break
        order = best
    original = list(range(1, len(matrix)))
    return order if cost(order, matrix, return_to_start) < cost(original, matrix, return_to_start) else original


def calculate(data):
    provider = DemoProvider() if data['mode'] == 'demo' else OSRMProvider()
    points = [data['start']] + data['stops']
    original_order = list(range(1, len(points)))
    order = optimize_order(provider.matrix(points), data['return_to_start'])

    def get_route(indices):
        indices = [0] + indices + ([0] if data['return_to_start'] else [])
        result = provider.route([points[i] for i in indices])
        result['itinerary'] = [dict(points[idx], original_index=idx, **leg) for idx, leg in zip(indices[1:], result['legs'])]
        result['order'] = indices
        return result

    original = get_route(original_order)
    optimized = get_route(order) if order != original_order else original
    # Recheck actual provider geometry/legs, not only the matrix objective.
    if optimized['distance'] > original['distance']:
        optimized = original
    return {'mode': data['mode'], 'label': provider.label, 'original': original, 'optimized': optimized,
            'saved_distance': original['distance'] - optimized['distance'], 'start': data['start'],
            'return_to_start': data['return_to_start']}
