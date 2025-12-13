class InMemoryRepository:
    def __init__(self):
        self._store = {}

    def add(self, data_type, records):
        self._store[data_type] = records

    def get_types(self):
        return list(self._store.keys())

    def filter_by_time(self, data_types, from_time, to_time):
        results = []
        for dt in data_types:
            for record in self._store.get(dt, []):
                if from_time <= record["time"] <= to_time:
                    results.append(record)
        return results
