// Copyright 2021 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CAST_STANDALONE_SENDER_STREAMING_ENCODER_UTIL_H_
#define CAST_STANDALONE_SENDER_STREAMING_ENCODER_UTIL_H_

#include <stdint.h>

namespace openscreen::cast {
void CopyPlane(const uint8_t* src,
               int src_stride,
               int num_rows,
               uint8_t* dst,
               int dst_stride);
}  // namespace openscreen::cast

#endif  // CAST_STANDALONE_SENDER_STREAMING_ENCODER_UTIL_H_
