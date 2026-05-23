package com.company.aiplatform.auth.service;

import java.util.Date;
import java.util.Set;

/**
 * Token 黑名单服务接口
 */
public interface ITokenBlacklistService {

    /** 将 Access Token 加入黑名单 */
    void blacklist(String tokenId, Date expirationDate);

    /** 检查 Token 是否在黑名单中 */
    boolean isBlacklisted(String tokenId);

    /** 批量检查 */
    Set<String> filterBlacklisted(Set<String> tokenIds);
}
