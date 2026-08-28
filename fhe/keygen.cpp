// keygen.cpp — hand-rolled key generation for StealthMatch.
//
// This replaces the @client @stage("key_generation") the DSL would normally
// emit. The DSL keygen unconditionally calls EvalSumKeyGen, which at the
// hardware ring dimension N=65536 generates a full log2(n_slots) rotation-key
// set (~150 MB in rk.bin) for cross-slot summation. StealthMatch's circuit is
// entirely per-slot (one opportunity per SIMD slot; no rotations, no sums), so
// it needs none of those keys. Hand-rolling keygen omits them, shrinking the
// on-disk keys and, more importantly, the Fog upload.
//
// The CKKS parameters below match the scheme block in client.niob exactly, so
// the serialized context stays consistent with the DSL-generated encrypt,
// score, and decrypt stages (they load cc.bin at runtime).
//
// Usage:  key_generation <size>   (size 0 = the sole Full profile, N=65536)

#include "nb_shared.h"

#include <cctype>
#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 2 || !std::isdigit(static_cast<unsigned char>(argv[1][0]))) {
        std::cout << "Usage: " << argv[0] << " instance-size\n";
        return argc < 2 ? 1 : 0;
    }
    auto inst = instance(static_cast<Profile>(std::stoi(argv[1])));

    // CKKS parameters — identical to client.niob's scheme block:
    // 128-classic security, uniform-ternary secret, multiplicative depth 2,
    // scaling modulus 42, first modulus 57, flexible-auto scaling, hybrid key
    // switching, ring dimension from the instance (65536).
    CCParams<CryptoContextCKKSRNS> parameters;
    parameters.SetSecretKeyDist(UNIFORM_TERNARY);
    parameters.SetSecurityLevel(HEStd_128_classic);
    parameters.SetMultiplicativeDepth(2);
    parameters.SetScalingModSize(42);
    parameters.SetFirstModSize(57);
    parameters.SetRingDim(inst.ring_dim);
    parameters.SetScalingTechnique(FLEXIBLEAUTO);
    parameters.SetKeySwitchTechnique(HYBRID);

    auto cc = GenCryptoContext(parameters);
    cc->Enable(PKE);
    cc->Enable(KEYSWITCH);
    cc->Enable(LEVELEDSHE);

    auto kp = cc->KeyGen();

    // Relinearization key: the squared-distance terms (difference * difference)
    // are cipher x cipher and need it. No rotation or sum keys are generated.
    cc->EvalMultKeyGen(kp.secretKey);

    auto keys_dir = keydir(inst);
    fs::create_directories(keys_dir);

    Serial::SerializeToFile(keys_dir / "cc.bin", cc, SerType::BINARY);
    Serial::SerializeToFile(keys_dir / "pk.bin", kp.publicKey, SerType::BINARY);
    Serial::SerializeToFile(keys_dir / "sk.bin", kp.secretKey, SerType::BINARY);
    {
        std::ofstream mk_file(keys_dir / "mk.bin", std::ios::out | std::ios::binary);
        cc->SerializeEvalMultKey(mk_file, SerType::BINARY);
    }
    // The generated score stage opens rk.bin, but this circuit uses no
    // automorphisms, so the file holds an empty automorphism-key set.
    {
        std::ofstream rk_file(keys_dir / "rk.bin", std::ios::out | std::ios::binary);
        cc->SerializeEvalAutomorphismKey(rk_file, SerType::BINARY);
    }

    std::cout << "[keygen] N=" << cc->GetRingDimension()
              << " depth=2 security=128-classic (relin only, no rotation/sum keys)\n";
    std::cout << "[keygen] wrote " << keys_dir << "/{cc,pk,sk,mk,rk}.bin\n";
    return 0;
}
