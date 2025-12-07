import os
import subprocess
import tempfile
import textwrap

import streamlit as st

st.set_page_config(page_title="Mini Compiler Visualizer", layout="wide")

st.title("🧠 Mini Compiler Visualizer (C + LLVM)")
st.write(
    "Left mein C code likho, phir **Run** dabao. Niche tabs mein "
    "compiler ke har stage ka output dekho: AST, IR, Optimized IR, Assembly."
)

default_code = textwrap.dedent(
    r"""
    int add(int a, int b) {
        return a + b;
    }

    int main() {
        int x = add(2, 3);
        return x;
    }
    """
).strip()

code = st.text_area("✍️ C source code:", value=default_code, height=220)

run = st.button("🚀 Run compiler pipeline")

ast_output = ""
ir_output = ""
opt_ir_output = ""
asm_output = ""
errors = []

def run_cmd(cmd, input_file=None):
    try:
        result = subprocess.run(
            cmd,
            stdin=subprocess.PIPE if input_file else None,
            text=True,
            capture_output=True,
            check=False,
        )
        out = result.stdout
        err = result.stderr
        return out, err
    except FileNotFoundError as e:
        return "", f"Command not found: {cmd[0]} ({e})"


if run:
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "source.c")
        ll_path = os.path.join(tmpdir, "source.ll")
        opt_bc_path = os.path.join(tmpdir, "opt.bc")
        opt_ll_path = os.path.join(tmpdir, "opt.ll")
        asm_path = os.path.join(tmpdir, "source.s")

        with open(src_path, "w") as f:
            f.write(code)

        ast_cmd = [
            "clang",
            "-Xclang",
            "-ast-dump",
            "-fsyntax-only",
            src_path,
        ]
        out, err = run_cmd(ast_cmd)
        ast_output = out or ""
        if err:
            errors.append(("AST / Syntax", err))

        ir_cmd = ["clang", "-S", "-emit-llvm", src_path, "-o", ll_path]
        _, err = run_cmd(ir_cmd)
        if err:
            errors.append(("IR generation", err))
        if os.path.exists(ll_path):
            with open(ll_path, "r") as f:
                ir_output = f.read()

        opt_cmd = ["opt", "-O3", ll_path, "-o", opt_bc_path]
        _, err = run_cmd(opt_cmd)
        if err:
            errors.append(("Optimization (opt -O3)", err))

        dis_cmd = ["llvm-dis", opt_bc_path, "-o", opt_ll_path]
        _, err = run_cmd(dis_cmd)
        if err:
            errors.append(("llvm-dis", err))

        if os.path.exists(opt_ll_path):
            with open(opt_ll_path, "r") as f:
                opt_ir_output = f.read()

        asm_cmd = ["clang", "-S", src_path, "-o", asm_path]
        _, err = run_cmd(asm_cmd)
        if err:
            errors.append(("Assembly generation", err))
        if os.path.exists(asm_path):
            with open(asm_path, "r") as f:
                asm_output = f.read()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📝 Source", "🌳 AST (Syntax Tree)", "⚙️ LLVM IR", "🧪 Optimized IR", "🧯 Assembly"]
)

with tab1:
    st.subheader("Source code")
    st.code(code, language="c")

with tab2:
    st.subheader("AST (Syntax Tree)")
    if ast_output:
        st.code(ast_output, language="text")
    else:
        st.write("Run button dabao to AST dikhega.")

with tab3:
    st.subheader("LLVM IR (Intermediate Representation)")
    if ir_output:
        st.code(ir_output, language="llvm")
    else:
        st.write("IR abhi generate nahi hua.")

with tab4:
    st.subheader("Optimized LLVM IR (-O3)")
    if opt_ir_output:
        st.code(opt_ir_output, language="llvm")
    else:
        st.write("Optimized IR abhi available nahi hai.")

with tab5:
    st.subheader("Assembly (Machine Code)")
    if asm_output:
        st.code(asm_output, language="asm")
    else:
        st.write("Assembly abhi generate nahi hua.")

if errors:
    st.markdown("### ⚠️ Compiler Messages")
    for stage, msg in errors:
        with st.expander(stage, expanded=False):
            st.code(msg, language="text")
