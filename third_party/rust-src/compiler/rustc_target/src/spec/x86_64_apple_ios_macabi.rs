use super::apple_base::{opts, Arch};
use crate::spec::{Cc, LinkerFlavor, Lld, SanitizerSet, StackProbeType, Target, TargetOptions};

pub fn target() -> Target {
    let llvm_target = "x86_64-apple-ios14.0-macabi";

    let arch = Arch::X86_64_macabi;
    let mut base = opts("ios", arch);
    base.add_pre_link_args(LinkerFlavor::Darwin(Cc::Yes, Lld::No), &["-target", llvm_target]);
    base.supported_sanitizers = SanitizerSet::ADDRESS | SanitizerSet::LEAK | SanitizerSet::THREAD;

    Target {
        llvm_target: llvm_target.into(),
        pointer_width: 64,
        data_layout:
            "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128".into(),
        arch: arch.target_arch(),
        options: TargetOptions {
            max_atomic_width: Some(128),
            stack_probes: StackProbeType::X86,
            ..base
        },
    }
}
