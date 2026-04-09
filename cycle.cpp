#include<iostream>
#include<utility>
#include<tuple>
#include<vector>

using namespace std;

template<typename Iterator>
class EnumerateIterator {
    size_t idx;
    Iterator iter;
public:
    EnumerateIterator(size_t i, Iterator it): idx(i), iter(it) {}

    auto operator*() {
        return pair<size_t, decltype(*iter)>(idx, *iter);
    }

    EnumerateIterator& operator++() {
        ++idx, ++iter;
        return *this;
    }

    bool operator!=(const EnumerateIterator& other) const {
        return iter != other.iter;
    }
};

template<typename Container>
class EnumerateRange {
    Container& ref;
public:
    explicit EnumerateRange(Container& c): ref(c) {}

    auto begin() { return EnumerateIterator(0, ref.begin()); }
    auto end() { return EnumerateIterator(ref.size(), ref.end()); }
};

template<typename Container>
EnumerateRange<Container> enumerate(Container& c) {
    return EnumerateRange<Container>(c);
}

template<typename... Iterators>
class ZipIterator {
    tuple<Iterators...> iters;
public:
    explicit ZipIterator(Iterators... its): iters(its...) {}

    auto operator*() {
        return apply([](auto&... it) {
            return tuple<decltype(*it)...>(*it...);
        }, iters);
    }

    ZipIterator& operator++() {
        apply([](auto&... it) {(++it, ...);}, iters);
        return *this;
    }

    bool operator!=(const ZipIterator& other) const {
        return get<0>(iters) != get<0>(other.iters);
    } 
};

template<typename... Containers>
class ZipRange {
    tuple<Containers&...> refs;
public:
    ZipRange(Containers&... cs): refs(cs...) {}

    auto begin() {
        return apply([](auto&... c) {
            return ZipIterator(c.begin()...);
        }, refs);
    }

    auto end() {
        return apply([](auto&... c) {
            return ZipIterator(c.end()...);
        }, refs);
    }
};

template<typename... Containers>
ZipRange<Containers...> zip(Containers&... cs) {
    return ZipRange<Containers...>(cs...);
}


int main() {
    vector<int> a{1, 2, 3};
    vector<string> b{"a", "b", "c"};
    vector<double> c{1.0, 2.0, 3.0}
    
    for (auto&& [i, v] : enumerate(a)) {
        cout << "i = " << i << " v = " << v << endl;
    }

    for (auto&& [x, y]: zip(a, b)) {
        cout << "x = " << x << " y = " << y << endl;
    }

    for (auto&& x: chain(a, b, c)) {
        cout << "x = " << x << endl;
    }
}
