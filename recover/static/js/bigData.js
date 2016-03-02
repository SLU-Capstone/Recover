/**
 * Created by matthew on 3/1/16.
 */
var NPOINTS = 100;

var Big = function(data) {
    this.data = sort(data)
};
Big.constructor = Big;

Big.prototype.getRange = function(begin, finish) {
    console.log('Entering getRange()');
    var start = Date.parse(begin);
    var end = Date.parse(finish);
    var lst = [];
    for (var i=0; i<this.data.length; i++) {
        var elem = this.data[i];
        var d = Date.parse(elem.x.replace(/-/g, "/"));
        if (d > start && d < end) {
            lst.push(elem);
        }
    }
    console.log('Leaving getRange()');
    console.log('Entering normalize()', lst.length);
    while (true) {
        console.log('wut');
        lst = normal(lst);
        if (lst.length < NPOINTS) {
            break;
        }
    }
    return lst;
};

normal = function(lst) {
    console.log('Recursion start normalize()');
    var norm = [];
    console.log(lst.length);
    for (var i=0; i<lst.length; i++) {
        if (i + 1 == lst.length) {
            break;
        }
        var ave = float(lst[i].y) + float(lst[i+1].y) / 2.0;
        var date = lst[i].x;
        norm.push({'x':date, 'y':ave});
        lst.splice(i+1,1);
    }
    console.log('Recursion end normalize()', norm.length);
    return norm;
};

sort = function(lst) {
    console.log('Entering sort()');
    lst.sort(function (a, b) {
        var aDate = Date.parse(a.x.replace(/-/g, "/"));
        var bDate = Date.parse(b.x.replace(/-/g, "/"));
        if (aDate < bDate) return -1;
        if (aDate > bDate) return 1;
        return 0;
    });
    console.log('Leaving sort()');
    return lst;
};

