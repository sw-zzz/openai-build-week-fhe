
# Hand-rolled key_generation target. The .niob omits the DSL keygen stage (its
# unconditional EvalSumKeyGen builds a large unused rotation-key set at N=65536),
# so keygen is compiled from fhe/keygen.cpp instead. `make build` appends this to
# the generated nb_out/CMakeLists.txt after each compile.
if(DEFINED LOCAL_SRC_DIR AND EXISTS "${LOCAL_SRC_DIR}/keygen.cpp")
  add_executable(key_generation ${LOCAL_SRC_DIR}/keygen.cpp ${SHARED_SRC})
endif()
