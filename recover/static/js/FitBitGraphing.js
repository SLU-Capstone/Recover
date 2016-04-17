// variables for smoothing factors in trend()
var ALPHA = 0.15;
var BETA = 0.15;

FitBitGraphing = function (heartRateData, averageHeartRate, stepsData, start, end) {

    // Convert to x-y format for Vis JS
    var allSteps = setup(stepsData, 0);
    var allHR = setup(averageHeartRate, 1);
    var HR = setup(heartRateData, 2, true);
    var n_groups = HR[HR.length - 1].group;
    var trends = trend(HR, n_groups);
    allHR = allHR.concat(HR);
    allHR = allHR.concat(trends);

    var HR_container = document.getElementById('HR_visualization');
    var STEP_container = document.getElementById('STEP_visualization');

    var HR_groups = new vis.DataSet();
    var STEP_groups = new vis.DataSet();

    for (var i = HR[0].group; i <= HR[HR.length - 1].group; i++) {
        console.log(i);
        HR_groups.add({
            id: i,
            content: "HR",
            style: 'stroke:red'
        });
    }
    for (var t = trends[0].group; t <= trends[trends.length - 1].group; t++) {
        console.log('at ', t);
        HR_groups.add({
            id: t,
            content: "HR Trend",
            style: 'stroke:blue'
        });
    }

    HR_groups.add({
        id: 1,
        content: "Average Resting HR",
        style: 'stroke:green'
    });

    STEP_groups.add({
        id: 0,
        content: "Step count"
    });

    var base_options = {
        start: start,
        end: end,
        //interpolation: true,
        drawPoints: false
    };
    var HR_options = clone(base_options);
    HR_options.dataAxis = {
        left: {
            range: {
                min: 35,
                max: 200
            }
        }
    };
    //HR_options.legend = true;
    var STEP_options = base_options;
    STEP_options.dataAxis = {
        left: {
            range: {
                min: -10,
                max: 1500
            }
        }
    };

    var graph2d = new vis.Graph2d(HR_container, allHR, HR_groups, HR_options);
    var step_graph = new vis.Graph2d(STEP_container, allSteps, STEP_groups, STEP_options);

};

var setup = function (data, group_start, inner_group) {
    inner_group = inner_group || false;
    var arr = [];
    for (var key in data) {
        if (data.hasOwnProperty(key)) {
            if (data[key] > 0) {
                arr.push({'x': key, 'y': data[key], group: group_start});
            }
        }
    }
    if (inner_group) return grouping(arr);
    return arr;
};

// Double Exponential smoothing algorithm with more weight on past events
var trend = function (data_arr, n_groups) {
    // set up for algorithm
    var alpha = ALPHA;
    var beta = BETA;
    var s = data_arr[1].y;
    var b = data_arr[1].y - data_arr[0].y;

    var group_num = 1;
    var arr = [{
        'x': data_arr[0].x,
        'y': data_arr[0].y,
        group: n_groups + group_num
    }, {
        'x': data_arr[1].x,
        'y': data_arr[1].y,
        group: n_groups + group_num
    }];
    var i = 2;
    for (var g = data_arr[0].group; g <= n_groups; g++) {
        console.log(group_num + n_groups, i);
        for (; i < data_arr.length - 1 && data_arr[i].group == g; i++) {

            var old_s = s;
            s = alpha * data_arr[i].y + (1 - alpha) * (s + b);
            b = beta * (s - old_s) + (1 - beta) * b;

            arr.push({
                'x': data_arr[i].x,
                'y': s,
                group: group_num + n_groups
            });
        }
        group_num++;
    }
    return arr;
};

var clone = function (obj) {
    if (null == obj || "object" != typeof obj) return obj;
    var copy = obj.constructor();
    for (var attr in obj) {
        if (obj.hasOwnProperty(attr)) copy[attr] = clone(obj[attr]);
    }
    return copy;
};

var grouping = function (data) {
    if (data.length !== 0) {
        data.sort(function (a, b) {
            var aDate = Date.parse(a.x.replace(/-/g, "/"));
            var bDate = Date.parse(b.x.replace(/-/g, "/"));
            if (aDate < bDate) return -1;
            if (aDate > bDate) return 1;
            return 0;
        });
        var grouped = [];
        var g = data[0].group;
        for (var i = 0; i < data.length - 1; i++) {
            var elem = data[i];
            var next = data[i + 1];
            var date1 = Date.parse(elem.x.replace(/-/g, "/"));
            var date2 = Date.parse(next.x.replace(/-/g, "/"));
            var diff = ((date2 - date1) / 1000) / 60;
            grouped.push({'x': elem.x, 'y': elem.y, group: g});
            data.group = g;
            if (diff > 15) {
                console.log(g, '-->', g + 1);
                g++;
            }
        }
        return grouped;
    }
    return data;
};
