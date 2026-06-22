"""Tests for complex real-world OpenSCAD scenarios."""
from openscad_lalr_parser import getASTfromString


class TestComplexScenarios:
    def test_complex_module(self):
        code = """
        module rounded_box(size=[10,10,10], r=1, center=false) {
            if (center) {
                translate(-size/2)
                    minkowski() {
                        cube(size - [2*r, 2*r, 2*r]);
                        sphere(r=r);
                    }
            } else {
                minkowski() {
                    cube(size - [2*r, 2*r, 2*r]);
                    sphere(r=r);
                }
            }
        }
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_complex_function(self):
        code = """
        function flatten(l) = [for (a = l) for (b = a) b];
        function sum(v, i=0) = i < len(v) ? v[i] + sum(v, i+1) : 0;
        function reverse(v) = [for (i = [len(v)-1 : -1 : 0]) v[i]];
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_nested_structures(self):
        code = """
        module assembly() {
            difference() {
                union() {
                    cube([20, 20, 5]);
                    translate([5, 5, 5])
                        cube([10, 10, 10]);
                }
                for (i = [0:3]) {
                    translate([5 + i * 3, 5 + i * 3, -1])
                        cylinder(h=7, r=1);
                }
            }
        }
        assembly();
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_complex_expression(self):
        code = """
        x = (a + b) * (c - d) / (e % f) + g ^ h;
        y = a > b ? (c <= d ? 1 : 2) : (e == f ? 3 : 4);
        z = !a && b || c != d;
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_complex_list_comprehension(self):
        code = """
        points = [for (i = [0:360]) [cos(i) * 10, sin(i) * 10]];
        filtered = [for (p = points) if (p.x > 0) p];
        nested = [for (i = [0:5]) for (j = [0:5]) [i, j, i*j]];
        with_let = [for (i = [0:10]) let(sq = i*i) if (sq < 50) sq];
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_module_with_all_features(self):
        code = """
        module fancy(size=10, count=5, enable=true) {
            w = size / count;
            if (enable) {
                for (i = [0:count-1]) {
                    let (offset = i * w) {
                        translate([offset, 0, 0])
                            cube([w * 0.8, w * 0.8, size]);
                    }
                }
            } else {
                echo("disabled");
                cube(size);
            }
        }
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_function_with_all_features(self):
        code = """
        function complex(v, depth=0) =
            depth > 10 ? v :
            let(
                half = len(v) / 2,
                left = [for (i = [0:half-1]) v[i]],
                right = [for (i = [half:len(v)-1]) v[i]]
            )
            concat(
                complex(left, depth + 1),
                complex(right, depth + 1)
            );
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0


class TestEdgeCases:
    def test_minimal_code(self):
        code = ";"
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)

    def test_only_comments(self):
        code = """
        // This is a comment
        /* This is a block comment */
        // Another comment
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)

    def test_only_use_include(self):
        code = """
        use <utils.scad>
        use <math.scad>
        include <config.scad>
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_very_long_expression(self):
        # Build a chain of additions: a0 + a1 + a2 + ... + a19
        terms = " + ".join(f"a{i}" for i in range(20))
        code = f"x = {terms};"
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_deeply_nested_parentheses(self):
        code = "x = ((((((((1 + 2))))))));"
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_multiple_operators(self):
        code = """
        a = 1 + 2 - 3 * 4 / 5 % 6;
        b = 1 == 2;
        c = 1 != 2;
        d = 1 < 2;
        e = 1 > 2;
        f = 1 <= 2;
        g = 1 >= 2;
        h = true && false;
        i = true || false;
        j = !true;
        k = 1 ? 2 : 3;
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_blocks(self):
        code = """
        module empty_mod() {}
        difference() {}
        union() {}
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0


class TestRealWorldExamples:
    def test_parametric_box(self):
        code = """
        // Parametric box with lid
        box_width = 50;
        box_depth = 30;
        box_height = 20;
        wall = 2;
        lid_height = 5;
        tolerance = 0.3;

        module box_base() {
            difference() {
                cube([box_width, box_depth, box_height]);
                translate([wall, wall, wall])
                    cube([box_width - 2*wall, box_depth - 2*wall, box_height]);
            }
        }

        module box_lid() {
            inner_w = box_width - 2*wall + tolerance;
            inner_d = box_depth - 2*wall + tolerance;
            union() {
                cube([box_width, box_depth, wall]);
                translate([(box_width - inner_w)/2, (box_depth - inner_d)/2, wall])
                    cube([inner_w, inner_d, lid_height - wall]);
            }
        }

        box_base();
        translate([box_width + 10, 0, 0])
            box_lid();
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_spiral_array(self):
        code = """
        n = 50;
        r = 30;
        h = 40;

        for (i = [0:n-1]) {
            angle = i * 360 / n;
            z = i * h / n;
            rotate([0, 0, angle])
                translate([r, 0, z])
                    sphere(r=2);
        }
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_helper_functions(self):
        code = """
        function lerp(a, b, t) = a + (b - a) * t;
        function clamp(x, lo, hi) = x < lo ? lo : (x > hi ? hi : x);
        function map_range(x, in_lo, in_hi, out_lo, out_hi) =
            lerp(out_lo, out_hi, (x - in_lo) / (in_hi - in_lo));
        function deg2rad(d) = d * 3.14159265 / 180;
        function rad2deg(r) = r * 180 / 3.14159265;

        echo(lerp(0, 10, 0.5));
        echo(clamp(15, 0, 10));
        echo(map_range(5, 0, 10, 100, 200));
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_utilities(self):
        code = """
        function head(v) = v[0];
        function tail(v) = len(v) > 1 ? [for (i = [1:len(v)-1]) v[i]] : [];
        function last(v) = v[len(v)-1];
        function take(v, n) = [for (i = [0:min(n, len(v))-1]) v[i]];
        function drop(v, n) = [for (i = [n:len(v)-1]) v[i]];
        function contains(v, x) = len([for (e = v) if (e == x) e]) > 0;
        function unique(v) = [for (i = [0:len(v)-1]) if (i == 0 || v[i] != v[i-1]) v[i]];

        test_v = [1, 2, 3, 4, 5];
        echo(head(test_v));
        echo(tail(test_v));
        echo(last(test_v));
        """
        result = getASTfromString(code)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
