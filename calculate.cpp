#include<iostream>
#include<numeric>
#include<string>
#include<vector>

using namespace std;

template<typename Container>
requires is_arithmetic_v<typename Container::value_type>
constexpr auto sum(const Container& c, typename Container::value_type init = {}) {
    return accumulate(c.begin(), c.end(), init);
}

template<typename T>
concept StringAppendable = requires(string s, T v) { s + v; };

template<typename Container>
requires StringAppendable<typename Container::value_type>
string join(const Container& c, const string& delimiter = "") {
    if (c.empty()) return "";

    auto it = c.begin();
    string result = *it++;

    while (it != c.end()) {
        result += delimiter;
        result += *it++;
    }
    return result;
}

template<typename Container, typename BinaryOp>
auto reduce(const Container& c, BinaryOp op, typename Container::value_type init = {}) {
    return accumulate(c.begin(), c.end(), init, op);
}


int main() {
    vector<int> nums = {1, 2, 3, 4, 5};
    cout << "sum: " << sum(nums, 10) << endl;

    vector<string> strs = {"hello", "world"};
    cout << "join: " << join(strs, "->") << endl;

    cout << "mul: " << reduce(nums, multiplies<int>(), 1) << endl;
}
