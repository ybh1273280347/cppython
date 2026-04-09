#include <iostream>
#include <vector>
#include <string>

namespace py {
    using namespace std;
    
    template<typename T>
    concept Container = requires(T t) {
        t.begin();
        t.end();
    };
    
    template<typename T>
    concept Printable = requires(T t) { cout << t; };
    
    template<Printable... Args>
    void print(const Args&... args) {
        bool first = true;
        ((first ? (first = false, cout << args) : (cout << " " << args)), ...);
        cout << "\n";
    }
    
    template<Container C>
    void print(const C& c, const string& sep = " ", const string& end = "\n", bool need_flush = false) {
        if (c.empty()) {
            need_flush? cout << end << flush: cout << end;
            return;
        }
        
        auto it = c.begin();
        cout << *it++;      
        while (it != c.end()) {
            cout << sep << *it++;
        }
        need_flush? cout << end << flush: cout << end;
    }
}

using namespace std;

int main() {
    vector<int> nums = {1, 2, 3};
    vector<string> strs = {"c++", "python"};
    
    py::print(nums);      // 1 2 3
    py::print(1, 2, 3);   // 1 2 3
    py::print(strs, " | ", " !!!\n");   // c++ | python !!!
    py::print("hello");   // hello
    
    return 0;
}